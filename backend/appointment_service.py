"""
Appointment Management Service.
Handles appointment scheduling, conflict detection (preventing doctor and patient double-booking),
status lifecycle updates, and clinical history queries.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, time
from database.connection import Database

class AppointmentService:
    """Manages outpatient appointment bookings with strict anti-double-booking guarantees."""

    @staticmethod
    def generate_appointment_code() -> str:
        """Generates a sequential appointment tracking code."""
        with Database() as db:
            row = db.execute_one("SELECT MAX(appointment_id) as max_id FROM appointments")
            next_id = (row['max_id'] or 0) + 1001
            return f"APP-{next_id:04d}"

    @classmethod
    def check_conflicts(
        cls,
        patient_id: int,
        doctor_id: int,
        appointment_date: str,
        appointment_time: str,
        exclude_appointment_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validates whether doctor or patient is already booked for the specified date and time.
        Returns (has_conflict_bool, message).
        """
        with Database() as db:
            # 1. Check Doctor conflict
            doc_query = """
                SELECT a.appointment_id, CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.doctor_id = %s 
                  AND a.appointment_date = %s 
                  AND a.appointment_time = %s
                  AND a.status = 'Scheduled'
            """
            params = [doctor_id, appointment_date, appointment_time]
            if exclude_appointment_id:
                doc_query += " AND a.appointment_id != %s"
                params.append(exclude_appointment_id)

            doc_conflict = db.execute_one(doc_query, tuple(params))
            if doc_conflict:
                return True, f"Conflict: {doc_conflict['doctor_name']} already has a scheduled appointment on {appointment_date} at {appointment_time}."

            # 2. Check Patient conflict
            pat_query = """
                SELECT a.appointment_id, CONCAT(p.first_name, ' ', p.last_name) as patient_name
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.patient_id = %s 
                  AND a.appointment_date = %s 
                  AND a.appointment_time = %s
                  AND a.status = 'Scheduled'
            """
            pat_params = [patient_id, appointment_date, appointment_time]
            if exclude_appointment_id:
                pat_query += " AND a.appointment_id != %s"
                pat_params.append(exclude_appointment_id)

            pat_conflict = db.execute_one(pat_query, tuple(pat_params))
            if pat_conflict:
                return True, f"Conflict: Patient {pat_conflict['patient_name']} already has another appointment on {appointment_date} at {appointment_time}."

            # 3. Check Doctor active status
            doc = db.execute_one("SELECT status FROM doctors WHERE doctor_id = %s", (doctor_id,))
            if doc and doc['status'] != 'Active':
                return True, f"Cannot book appointment: Doctor is currently marked as '{doc['status']}'."

            return False, "No conflict detected."

    @classmethod
    def schedule_appointment(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Schedules a new appointment after running conflict prevention algorithms."""
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        appointment_date = str(data.get("appointment_date", "")).strip()
        appointment_time = str(data.get("appointment_time", "")).strip()
        reason = data.get("reason", "").strip()

        if not patient_id or not doctor_id or not appointment_date or not appointment_time:
            return False, "Patient, Doctor, Date, and Time are all required.", None

        # Check double booking
        has_conflict, conflict_msg = cls.check_conflicts(patient_id, doctor_id, appointment_date, appointment_time)
        if has_conflict:
            return False, conflict_msg, None

        appointment_code = data.get("appointment_code") or cls.generate_appointment_code()

        try:
            with Database() as db:
                query = """
                    INSERT INTO appointments (
                        appointment_code, patient_id, doctor_id, appointment_date,
                        appointment_time, reason, status, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    appointment_code,
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    reason,
                    data.get("status", "Scheduled"),
                    data.get("notes", "").strip() or None
                )
                app_id = db.execute_insert(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("APPOINTMENT_SCHEDULED", "Appointment", appointment_code, f"Booked for {appointment_date} at {appointment_time}")
                )
                return True, f"Appointment {appointment_code} scheduled successfully.", app_id
        except Exception as e:
            return False, f"Failed to schedule appointment: {str(e)}", None

    @classmethod
    def update_appointment(cls, appointment_id: int, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Updates appointment details with conflict re-validation."""
        patient_id = data.get("patient_id")
        doctor_id = data.get("doctor_id")
        appointment_date = str(data.get("appointment_date", "")).strip()
        appointment_time = str(data.get("appointment_time", "")).strip()
        status = data.get("status", "Scheduled")

        if not patient_id or not doctor_id or not appointment_date or not appointment_time:
            return False, "Patient, Doctor, Date, and Time are all required."

        if status == 'Scheduled':
            has_conflict, conflict_msg = cls.check_conflicts(
                patient_id, doctor_id, appointment_date, appointment_time, exclude_appointment_id=appointment_id
            )
            if has_conflict:
                return False, conflict_msg

        try:
            with Database() as db:
                query = """
                    UPDATE appointments
                    SET patient_id = %s, doctor_id = %s, appointment_date = %s,
                        appointment_time = %s, reason = %s, status = %s, notes = %s
                    WHERE appointment_id = %s
                """
                params = (
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    data.get("reason", "").strip(),
                    status,
                    data.get("notes", "").strip() or None,
                    appointment_id
                )
                db.execute_non_query(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("APPOINTMENT_UPDATED", "Appointment", str(appointment_id), f"Status updated to '{status}'")
                )
                return True, "Appointment updated successfully."
        except Exception as e:
            return False, f"Update failed: {str(e)}"

    @classmethod
    def update_status(cls, appointment_id: int, new_status: str, notes: Optional[str] = None) -> Tuple[bool, str]:
        """Convenience method to transition appointment status (e.g. Completed, Cancelled)."""
        valid_statuses = ('Scheduled', 'Completed', 'Cancelled', 'No-Show')
        if new_status not in valid_statuses:
            return False, f"Invalid status '{new_status}'. Must be one of {valid_statuses}."

        try:
            with Database() as db:
                if notes:
                    query = "UPDATE appointments SET status = %s, notes = CONCAT(COALESCE(notes, ''), '\n', %s) WHERE appointment_id = %s"
                    params = (new_status, notes, appointment_id)
                else:
                    query = "UPDATE appointments SET status = %s WHERE appointment_id = %s"
                    params = (new_status, appointment_id)

                db.execute_non_query(query, params)
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    (f"APPOINTMENT_{new_status.upper()}", "Appointment", str(appointment_id), f"Changed status to {new_status}")
                )
                return True, f"Appointment status changed to {new_status}."
        except Exception as e:
            return False, f"Failed to update appointment status: {str(e)}"

    @classmethod
    def get_all_appointments(
        cls,
        search_term: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries appointments joined with patient and doctor details."""
        with Database() as db:
            conditions = []
            params = []

            if search_term:
                term = f"%{search_term.strip()}%"
                conditions.append("""
                    (a.appointment_code LIKE %s 
                     OR p.first_name LIKE %s OR p.last_name LIKE %s 
                     OR d.first_name LIKE %s OR d.last_name LIKE %s
                     OR a.reason LIKE %s)
                """)
                params.extend([term, term, term, term, term, term])

            if status and status != "All":
                conditions.append("a.status = %s")
                params.append(status)

            if date_filter:
                conditions.append("a.appointment_date = %s")
                params.append(date_filter)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            query = f"""
                SELECT a.appointment_id, a.appointment_code, a.appointment_date, a.appointment_time,
                       a.reason, a.status, a.notes, a.created_at,
                       a.patient_id, p.patient_code,
                       CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       p.phone as patient_phone,
                       a.doctor_id, d.doctor_code,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                       d.specialization, d.department, d.consultation_fee
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                {where_clause}
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
            return db.execute_query(query, tuple(params))
