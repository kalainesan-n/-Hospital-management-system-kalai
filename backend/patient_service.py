"""
Patient Management Service.
Handles CRUD, validation, search, and historical appointment/admission tracking.
"""

from typing import List, Dict, Any, Optional, Tuple
from database.connection import Database
from datetime import date, datetime

class PatientService:
    """Manages patient records and related historical summaries."""

    @staticmethod
    def generate_patient_code() -> str:
        """Generates a sequential or timestamp-based unique patient code."""
        with Database() as db:
            row = db.execute_one("SELECT MAX(patient_id) as max_id FROM patients")
            next_id = (row['max_id'] or 0) + 1
            return f"PAT-{next_id:04d}"

    @classmethod
    def get_all_patients(cls, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all patients or filters by search term (code, name, phone, email)."""
        with Database() as db:
            if search_term:
                term = f"%{search_term.strip()}%"
                query = """
                    SELECT patient_id, patient_code, first_name, last_name, 
                           CONCAT(first_name, ' ', last_name) as full_name,
                           date_of_birth, age, gender, phone, email, address,
                           blood_group, emergency_contact, medical_history, created_at
                    FROM patients
                    WHERE patient_code LIKE %s 
                       OR first_name LIKE %s 
                       OR last_name LIKE %s 
                       OR phone LIKE %s 
                       OR email LIKE %s
                    ORDER BY patient_id DESC
                """
                return db.execute_query(query, (term, term, term, term, term))
            else:
                query = """
                    SELECT patient_id, patient_code, first_name, last_name,
                           CONCAT(first_name, ' ', last_name) as full_name,
                           date_of_birth, age, gender, phone, email, address,
                           blood_group, emergency_contact, medical_history, created_at
                    FROM patients
                    ORDER BY patient_id DESC
                """
                return db.execute_query(query)

    @classmethod
    def get_patient_by_id(cls, patient_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single patient record by primary key."""
        with Database() as db:
            query = """
                SELECT patient_id, patient_code, first_name, last_name,
                       CONCAT(first_name, ' ', last_name) as full_name,
                       date_of_birth, age, gender, phone, email, address,
                       blood_group, emergency_contact, medical_history, created_at
                FROM patients
                WHERE patient_id = %s
            """
            return db.execute_one(query, (patient_id,))

    @classmethod
    def create_patient(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Validates and persists a new patient record."""
        # Validation
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()

        if not first_name or not last_name:
            return False, "First name and last name are required.", None
        if not phone:
            return False, "Phone number is required.", None

        patient_code = data.get("patient_code") or cls.generate_patient_code()

        try:
            with Database() as db:
                query = """
                    INSERT INTO patients (
                        patient_code, first_name, last_name, date_of_birth, age,
                        gender, phone, email, address, blood_group, emergency_contact, medical_history
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    patient_code,
                    first_name,
                    last_name,
                    data.get("date_of_birth") or None,
                    data.get("age") or None,
                    data.get("gender", "Other"),
                    phone,
                    data.get("email", "").strip() or None,
                    data.get("address", "").strip() or None,
                    data.get("blood_group", "").strip() or None,
                    data.get("emergency_contact", "").strip() or None,
                    data.get("medical_history", "").strip() or None
                )
                pid = db.execute_insert(query, params)

                # Log activity
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("PATIENT_CREATED", "Patient", patient_code, f"Added patient {first_name} {last_name}")
                )
                return True, f"Patient {patient_code} created successfully.", pid
        except Exception as e:
            return False, f"Failed to create patient: {str(e)}", None

    @classmethod
    def update_patient(cls, patient_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Updates existing patient details."""
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        phone = data.get("phone", "").strip()

        if not first_name or not last_name or not phone:
            return False, "First name, last name, and phone cannot be empty."

        try:
            with Database() as db:
                query = """
                    UPDATE patients
                    SET first_name = %s, last_name = %s, date_of_birth = %s, age = %s,
                        gender = %s, phone = %s, email = %s, address = %s,
                        blood_group = %s, emergency_contact = %s, medical_history = %s
                    WHERE patient_id = %s
                """
                params = (
                    first_name,
                    last_name,
                    data.get("date_of_birth") or None,
                    data.get("age") or None,
                    data.get("gender", "Other"),
                    phone,
                    data.get("email", "").strip() or None,
                    data.get("address", "").strip() or None,
                    data.get("blood_group", "").strip() or None,
                    data.get("emergency_contact", "").strip() or None,
                    data.get("medical_history", "").strip() or None,
                    patient_id
                )
                affected = db.execute_non_query(query, params)
                if affected > 0:
                    db.execute_non_query(
                        "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                        ("PATIENT_UPDATED", "Patient", str(patient_id), f"Updated profile for {first_name} {last_name}")
                    )
                    return True, "Patient profile updated successfully."
                return False, "No changes made or patient not found."
        except Exception as e:
            return False, f"Failed to update patient: {str(e)}"

    @classmethod
    def delete_patient(cls, patient_id: int) -> Tuple[bool, str]:
        """Safely removes a patient record if no foreign key constraints are violated."""
        try:
            with Database() as db:
                # Check for active admissions
                active_adm = db.execute_one(
                    "SELECT COUNT(*) as count FROM admissions WHERE patient_id = %s AND status = 'Admitted'",
                    (patient_id,)
                )
                if active_adm and active_adm['count'] > 0:
                    return False, "Cannot delete patient with an active hospital admission."

                # Check for scheduled appointments
                active_apps = db.execute_one(
                    "SELECT COUNT(*) as count FROM appointments WHERE patient_id = %s AND status = 'Scheduled'",
                    (patient_id,)
                )
                if active_apps and active_apps['count'] > 0:
                    return False, "Cannot delete patient with upcoming scheduled appointments."

                # Retrieve code for log
                pat = db.execute_one("SELECT patient_code, first_name, last_name FROM patients WHERE patient_id = %s", (patient_id,))
                code = pat['patient_code'] if pat else str(patient_id)

                db.execute_non_query("DELETE FROM patients WHERE patient_id = %s", (patient_id,))
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("PATIENT_DELETED", "Patient", code, f"Deleted patient record ID {patient_id}")
                )
                return True, "Patient deleted successfully."
        except Exception as e:
            return False, f"Delete failed: {str(e)}"

    @classmethod
    def get_patient_history(cls, patient_id: int) -> Dict[str, Any]:
        """Gathers appointment and admission history for a given patient."""
        with Database() as db:
            patient = db.execute_one("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
            appointments = db.execute_query("""
                SELECT a.appointment_code, a.appointment_date, a.appointment_time, 
                       a.reason, a.status, a.notes,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                       d.specialization
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """, (patient_id,))

            admissions = db.execute_query("""
                SELECT adm.admission_code, adm.admission_date, adm.discharge_date,
                       adm.diagnosis, adm.admission_type, adm.status, adm.discharge_summary,
                       adm.total_amount, b.bed_number, b.ward_name,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM admissions adm
                JOIN beds b ON adm.bed_id = b.bed_id
                JOIN doctors d ON adm.doctor_id = d.doctor_id
                WHERE adm.patient_id = %s
                ORDER BY adm.admission_date DESC
            """, (patient_id,))

            return {
                "patient": patient,
                "appointments": appointments,
                "admissions": admissions
            }
