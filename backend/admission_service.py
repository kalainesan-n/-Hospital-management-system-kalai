"""
Admission and Discharge Management Service.
Handles in-patient admissions, automated bed locking/releasing upon discharge,
and full financial and diagnostic history preservation.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database.connection import Database

class AdmissionService:
    """Manages patient hospitalizations, bed link transactions, and discharge routines."""

    @staticmethod
    def generate_admission_code() -> str:
        """Generates a unique sequential admission code."""
        with Database() as db:
            row = db.execute_one("SELECT MAX(admission_id) as max_id FROM admissions")
            next_id = (row['max_id'] or 0) + 5001
            return f"ADM-{next_id:04d}"

    @classmethod
    def get_all_admissions(
        cls,
        search_term: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries admissions joined with patient, bed, and doctor data."""
        with Database() as db:
            conditions = []
            params = []

            if search_term:
                term = f"%{search_term.strip()}%"
                conditions.append("""
                    (adm.admission_code LIKE %s
                     OR p.first_name LIKE %s OR p.last_name LIKE %s OR p.patient_code LIKE %s
                     OR b.bed_number LIKE %s OR b.ward_name LIKE %s
                     OR adm.diagnosis LIKE %s)
                """)
                params.extend([term, term, term, term, term, term, term])

            if status and status != "All":
                conditions.append("adm.status = %s")
                params.append(status)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT adm.admission_id, adm.admission_code, adm.patient_id, adm.bed_id, adm.doctor_id,
                       adm.admission_date, adm.discharge_date, adm.diagnosis, adm.admission_type,
                       adm.status, adm.discharge_summary, adm.total_amount, adm.created_at,
                       p.patient_code, CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       p.gender as patient_gender, p.age as patient_age, p.phone as patient_phone,
                       b.bed_number, b.ward_name, b.bed_type, b.daily_charge,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                       d.specialization as doctor_specialization
                FROM admissions adm
                JOIN patients p ON adm.patient_id = p.patient_id
                JOIN beds b ON adm.bed_id = b.bed_id
                JOIN doctors d ON adm.doctor_id = d.doctor_id
                {where_clause}
                ORDER BY adm.admission_date DESC
            """
            return db.execute_query(query, tuple(params))

    @classmethod
    def get_admission_by_id(cls, admission_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a specific admission record."""
        with Database() as db:
            query = """
                SELECT adm.*, 
                       p.patient_code, CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       b.bed_number, b.ward_name, b.daily_charge,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM admissions adm
                JOIN patients p ON adm.patient_id = p.patient_id
                JOIN beds b ON adm.bed_id = b.bed_id
                JOIN doctors d ON adm.doctor_id = d.doctor_id
                WHERE adm.admission_id = %s
            """
            return db.execute_one(query, (admission_id,))

    @classmethod
    def admit_patient(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Admits a patient and marks bed as Occupied inside an atomic database transaction.
        Prevents duplicate active admissions for the same patient.
        """
        patient_id = data.get("patient_id")
        bed_id = data.get("bed_id")
        doctor_id = data.get("doctor_id")
        admission_date = data.get("admission_date") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diagnosis = data.get("diagnosis", "").strip()

        if not patient_id or not bed_id or not doctor_id or not diagnosis:
            return False, "Patient, Bed, Doctor, and Diagnosis are required for admission.", None

        try:
            with Database() as db:
                # 1. Check if patient is already actively admitted
                already_admitted = db.execute_one(
                    "SELECT admission_id, admission_code FROM admissions WHERE patient_id = %s AND status = 'Admitted'",
                    (patient_id,)
                )
                if already_admitted:
                    return False, f"Patient is already admitted under admission record {already_admitted['admission_code']}.", None

                # 2. Check bed availability with row locking
                bed = db.execute_one("SELECT bed_number, status FROM beds WHERE bed_id = %s FOR UPDATE", (bed_id,))
                if not bed:
                    return False, "Selected bed does not exist.", None
                if bed['status'] != 'Available':
                    return False, f"Bed {bed['bed_number']} is not available (Current status: {bed['status']}).", None

                admission_code = data.get("admission_code") or cls.generate_admission_code()

                # 3. Insert admission record
                query = """
                    INSERT INTO admissions (
                        admission_code, patient_id, bed_id, doctor_id, admission_date,
                        diagnosis, admission_type, status, total_amount
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Admitted', %s)
                """
                params = (
                    admission_code,
                    patient_id,
                    bed_id,
                    doctor_id,
                    admission_date,
                    diagnosis,
                    data.get("admission_type", "Routine"),
                    float(data.get("total_amount") or 0.0)
                )
                adm_id = db.execute_insert(query, params)

                # 4. Mark bed as Occupied
                db.execute_non_query("UPDATE beds SET status = 'Occupied' WHERE bed_id = %s", (bed_id,))

                # 5. Log activity
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("PATIENT_ADMITTED", "Admission", admission_code, f"Patient admitted to bed {bed['bed_number']}.")
                )

                return True, f"Patient successfully admitted under {admission_code}.", adm_id
        except Exception as e:
            return False, f"Admission failed: {str(e)}", None

    @classmethod
    def discharge_patient(
        cls,
        admission_id: int,
        discharge_date: Optional[str] = None,
        discharge_summary: Optional[str] = None,
        total_amount: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Discharges a patient and automatically releases the bed back to Available.
        Preserves all medical and financial history.
        """
        discharge_dt = discharge_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with Database() as db:
                adm = db.execute_one(
                    "SELECT admission_id, admission_code, bed_id, status FROM admissions WHERE admission_id = %s FOR UPDATE",
                    (admission_id,)
                )
                if not adm:
                    return False, "Admission record not found."
                if adm['status'] == 'Discharged':
                    return False, "Patient has already been discharged."

                bed_id = adm['bed_id']

                # Update admission to Discharged
                query = """
                    UPDATE admissions
                    SET status = 'Discharged', discharge_date = %s,
                        discharge_summary = %s, total_amount = COALESCE(%s, total_amount)
                    WHERE admission_id = %s
                """
                db.execute_non_query(query, (discharge_dt, discharge_summary or "Discharged in stable condition.", total_amount, admission_id))

                # Automatically release bed to Available
                db.execute_non_query("UPDATE beds SET status = 'Available' WHERE bed_id = %s", (bed_id,))

                # Log activity
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("PATIENT_DISCHARGED", "Admission", adm['admission_code'], f"Discharged and bed {bed_id} released.")
                )

                return True, f"Admission {adm['admission_code']} discharged successfully and bed released."
        except Exception as e:
            return False, f"Discharge failed: {str(e)}"
