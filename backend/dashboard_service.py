"""
Dashboard Metrics Service.
Executes live aggregate MySQL queries to calculate real-time operational statistics,
occupancy rates, active clinical caseloads, and audit trail logs.
"""

from typing import Dict, Any, List
from datetime import date
from database.connection import Database

class DashboardService:
    """Provides aggregated live hospital statistics for the administrative dashboard."""

    @classmethod
    def get_live_metrics(cls) -> Dict[str, Any]:
        """
        Calculates all dashboard KPIs directly from the MySQL database:
        - Total Patients
        - Total Doctors (and Active doctors)
        - Today's Appointments & Total Appointments
        - Available, Occupied, Maintenance, and Total Beds
        - Bed Occupancy Percentage
        - Active Inpatient Admissions
        - Pending Triage Emergencies
        """
        with Database() as db:
            today_str = date.today().strftime("%Y-%m-%d")

            # 1. Patients Count
            pat_row = db.execute_one("SELECT COUNT(*) as count FROM patients")
            total_patients = pat_row['count'] if pat_row else 0

            # 2. Doctors Count
            doc_row = db.execute_one("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active FROM doctors")
            total_doctors = int(doc_row['total']) if doc_row and doc_row['total'] is not None else 0
            active_doctors = int(doc_row['active']) if doc_row and doc_row['active'] is not None else 0

            # 3. Appointments Count
            app_today_row = db.execute_one(
                "SELECT COUNT(*) as count FROM appointments WHERE appointment_date = %s",
                (today_str,)
            )
            today_appointments = app_today_row['count'] if app_today_row else 0

            app_total_row = db.execute_one("SELECT COUNT(*) as count FROM appointments")
            total_appointments = app_total_row['count'] if app_total_row else 0

            # 4. Beds & Occupancy
            bed_row = db.execute_one("""
                SELECT 
                    COUNT(*) as total_beds,
                    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available_beds,
                    SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied_beds,
                    SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance_beds
                FROM beds
            """)
            total_beds = int(bed_row['total_beds']) if bed_row and bed_row['total_beds'] is not None else 0
            available_beds = int(bed_row['available_beds']) if bed_row and bed_row['available_beds'] is not None else 0
            occupied_beds = int(bed_row['occupied_beds']) if bed_row and bed_row['occupied_beds'] is not None else 0
            maintenance_beds = int(bed_row['maintenance_beds']) if bed_row and bed_row['maintenance_beds'] is not None else 0

            occupancy_pct = (float(occupied_beds) / float(total_beds) * 100.0) if total_beds > 0 else 0.0

            # 5. Active Admissions
            adm_row = db.execute_one("SELECT COUNT(*) as count FROM admissions WHERE status = 'Admitted'")
            active_admissions = adm_row['count'] if adm_row else 0

            # 6. Pending Emergencies
            emg_row = db.execute_one("SELECT COUNT(*) as count FROM emergency_cases WHERE status = 'Pending'")
            pending_emergencies = emg_row['count'] if emg_row else 0

            # 7. Critical emergencies count
            emg_crit_row = db.execute_one("SELECT COUNT(*) as count FROM emergency_cases WHERE status = 'Pending' AND triage_severity = 'Critical'")
            critical_emergencies = emg_crit_row['count'] if emg_crit_row else 0

            return {
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "active_doctors": active_doctors,
                "today_appointments": today_appointments,
                "total_appointments": total_appointments,
                "total_beds": total_beds,
                "available_beds": available_beds,
                "occupied_beds": occupied_beds,
                "maintenance_beds": maintenance_beds,
                "bed_occupancy_pct": round(occupancy_pct, 1),
                "active_admissions": active_admissions,
                "pending_emergencies": pending_emergencies,
                "critical_emergencies": critical_emergencies
            }

    @classmethod
    def get_recent_activity(cls, limit: int = 8) -> List[Dict[str, Any]]:
        """Fetches the most recent system activity logs."""
        with Database() as db:
            query = """
                SELECT log_id, action, entity_type, entity_id, details, performed_by, created_at
                FROM activity_logs
                ORDER BY created_at DESC, log_id DESC
                LIMIT %s
            """
            return db.execute_query(query, (limit,))

    @classmethod
    def get_today_appointments_preview(cls, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetches upcoming appointments for today."""
        with Database() as db:
            today_str = date.today().strftime("%Y-%m-%d")
            query = """
                SELECT a.appointment_code, a.appointment_time, a.status,
                       CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                       d.department
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                WHERE a.appointment_date = %s
                ORDER BY a.appointment_time ASC
                LIMIT %s
            """
            return db.execute_query(query, (today_str, limit))
