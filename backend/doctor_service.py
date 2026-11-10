"""
Doctor Management Service.
Handles CRUD, availability scheduling, department listings, and doctor appointment histories.
"""

from typing import List, Dict, Any, Optional, Tuple
from database.connection import Database

class DoctorService:
    """Manages doctor profiles, qualifications, schedules, and clinical assignments."""

    @staticmethod
    def generate_doctor_code() -> str:
        """Generates a sequential doctor code."""
        with Database() as db:
            row = db.execute_one("SELECT MAX(doctor_id) as max_id FROM doctors")
            next_id = (row['max_id'] or 0) + 1
            return f"DOC-{next_id:03d}"

    @classmethod
    def get_all_doctors(
        cls,
        search_term: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves doctors with optional filtering by search text, department, and status."""
        with Database() as db:
            conditions = []
            params = []

            if search_term:
                term = f"%{search_term.strip()}%"
                conditions.append("(doctor_code LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR specialization LIKE %s)")
                params.extend([term, term, term, term])

            if department and department != "All":
                conditions.append("department = %s")
                params.append(department)

            if status and status != "All":
                conditions.append("status = %s")
                params.append(status)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT doctor_id, doctor_code, first_name, last_name,
                       CONCAT('Dr. ', first_name, ' ', last_name) as full_name,
                       specialization, department, phone, email, qualification,
                       consultation_fee, available_days, shift_time, status, created_at
                FROM doctors
                {where_clause}
                ORDER BY doctor_id ASC
            """
            return db.execute_query(query, tuple(params))

    @classmethod
    def get_doctor_by_id(cls, doctor_id: int) -> Optional[Dict[str, Any]]:
        """Fetches a single doctor by primary key."""
        with Database() as db:
            query = """
                SELECT doctor_id, doctor_code, first_name, last_name,
                       CONCAT('Dr. ', first_name, ' ', last_name) as full_name,
                       specialization, department, phone, email, qualification,
                       consultation_fee, available_days, shift_time, status, created_at
                FROM doctors
                WHERE doctor_id = %s
            """
            return db.execute_one(query, (doctor_id,))

    @classmethod
    def create_doctor(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Validates and creates a new doctor record."""
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        specialization = data.get("specialization", "").strip()
        department = data.get("department", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()

        if not first_name or not last_name or not specialization or not department or not phone:
            return False, "First name, last name, specialization, department, and phone are required.", None

        doctor_code = data.get("doctor_code") or cls.generate_doctor_code()

        try:
            with Database() as db:
                query = """
                    INSERT INTO doctors (
                        doctor_code, first_name, last_name, specialization, department,
                        phone, email, qualification, consultation_fee, available_days,
                        shift_time, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                fee = float(data.get("consultation_fee") or 500.0)
                params = (
                    doctor_code,
                    first_name,
                    last_name,
                    specialization,
                    department,
                    phone,
                    email,
                    data.get("qualification", "").strip() or None,
                    fee,
                    data.get("available_days", "Mon,Tue,Wed,Thu,Fri"),
                    data.get("shift_time", "09:00 AM - 05:00 PM"),
                    data.get("status", "Active")
                )
                doc_id = db.execute_insert(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("DOCTOR_CREATED", "Doctor", doctor_code, f"Registered Dr. {first_name} {last_name} ({specialization})")
                )
                return True, f"Doctor {doctor_code} registered successfully.", doc_id
        except Exception as e:
            return False, f"Failed to register doctor: {str(e)}", None

    @classmethod
    def update_doctor(cls, doctor_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Updates doctor details."""
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        specialization = data.get("specialization", "").strip()
        department = data.get("department", "").strip()
        phone = data.get("phone", "").strip()

        if not first_name or not last_name or not specialization or not department or not phone:
            return False, "First name, last name, specialization, department, and phone are required."

        try:
            with Database() as db:
                query = """
                    UPDATE doctors
                    SET first_name = %s, last_name = %s, specialization = %s,
                        department = %s, phone = %s, email = %s, qualification = %s,
                        consultation_fee = %s, available_days = %s, shift_time = %s,
                        status = %s
                    WHERE doctor_id = %s
                """
                fee = float(data.get("consultation_fee") or 500.0)
                params = (
                    first_name,
                    last_name,
                    specialization,
                    department,
                    phone,
                    data.get("email", "").strip(),
                    data.get("qualification", "").strip(),
                    fee,
                    data.get("available_days", "Mon,Tue,Wed,Thu,Fri"),
                    data.get("shift_time", "09:00 AM - 05:00 PM"),
                    data.get("status", "Active"),
                    doctor_id
                )
                db.execute_non_query(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("DOCTOR_UPDATED", "Doctor", str(doctor_id), f"Updated Dr. {first_name} {last_name}")
                )
                return True, "Doctor profile updated successfully."
        except Exception as e:
            return False, f"Update failed: {str(e)}"

    @classmethod
    def delete_doctor(cls, doctor_id: int) -> Tuple[bool, str]:
        """Safely removes a doctor if there are no existing appointments or active admissions."""
        try:
            with Database() as db:
                apps = db.execute_one(
                    "SELECT COUNT(*) as count FROM appointments WHERE doctor_id = %s AND status = 'Scheduled'",
                    (doctor_id,)
                )
                if apps and apps['count'] > 0:
                    return False, "Cannot delete doctor with upcoming scheduled appointments."

                adms = db.execute_one(
                    "SELECT COUNT(*) as count FROM admissions WHERE doctor_id = %s AND status = 'Admitted'",
                    (doctor_id,)
                )
                if adms and adms['count'] > 0:
                    return False, "Cannot delete doctor currently treating admitted patients."

                doc = db.execute_one("SELECT doctor_code, first_name, last_name FROM doctors WHERE doctor_id = %s", (doctor_id,))
                code = doc['doctor_code'] if doc else str(doctor_id)

                db.execute_non_query("DELETE FROM doctors WHERE doctor_id = %s", (doctor_id,))
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("DOCTOR_DELETED", "Doctor", code, f"Removed doctor record ID {doctor_id}")
                )
                return True, "Doctor removed successfully."
        except Exception as e:
            return False, f"Delete failed: {str(e)}"

    @classmethod
    def get_doctor_appointments(cls, doctor_id: int) -> List[Dict[str, Any]]:
        """Retrieves appointments assigned to a specific doctor."""
        with Database() as db:
            query = """
                SELECT a.appointment_id, a.appointment_code, a.appointment_date, a.appointment_time,
                       a.reason, a.status, a.notes,
                       p.patient_code, CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       p.phone as patient_phone
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.doctor_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
            return db.execute_query(query, (doctor_id,))

    @classmethod
    def get_departments(cls) -> List[str]:
        """Returns unique doctor departments currently registered."""
        with Database() as db:
            rows = db.execute_query("SELECT DISTINCT department FROM doctors ORDER BY department ASC")
            return [r['department'] for r in rows if r.get('department')]
