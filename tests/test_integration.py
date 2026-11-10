"""
End-to-End System Integration Tests.
Exercises live MySQL operations across all 10 modules:
- Admin Auth
- Patient CRUD & History
- Doctor CRUD & Schedules
- Appointment Scheduling & Double-Booking Prevention
- Bed Allocation & Double-Allocation Prevention
- Inpatient Admission & Automated Bed Release upon Discharge
- Emergency Min-Heap Priority Queue & Case Processing
- Dashboard Live Metric Calculations
- Analytics Pandas DataFrame Generations
- Tabular Reports & CSV File Generation
- Database Persistence Verification
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import date, datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.auth_service import AuthService
from backend.patient_service import PatientService
from backend.doctor_service import DoctorService
from backend.appointment_service import AppointmentService
from backend.bed_service import BedService
from backend.admission_service import AdmissionService
from backend.emergency_service import EmergencyService, EmergencyPriorityQueue
from backend.dashboard_service import DashboardService
from backend.analytics_service import AnalyticsService
from backend.report_service import ReportService
from database.connection import Database

class TestSystemIntegration(unittest.TestCase):
    """Full integration test suite against live MySQL database."""

    def test_01_authentication(self):
        """Tests admin login success, rejection of bad credentials, and session state."""
        # Valid login
        success, msg, user = AuthService.login("admin", "admin123")
        self.assertTrue(success, f"Login failed: {msg}")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "admin")
        self.assertTrue(AuthService.is_authenticated())

        # Bad password
        bad_succ, bad_msg, _ = AuthService.login("admin", "wrong_password_999")
        self.assertFalse(bad_succ)

        # Logout
        AuthService.logout()
        self.assertFalse(AuthService.is_authenticated())

    def test_02_patient_crud_and_history(self):
        """Tests patient creation, search, update, history retrieval, and cleanup."""
        # 1. Create Patient
        test_patient = {
            "first_name": "Integration",
            "last_name": "Tester",
            "age": 35,
            "gender": "Female",
            "phone": "9998887776",
            "email": "integration.test@hospital.org",
            "address": "100 QA Laboratory Lane",
            "blood_group": "AB+",
            "emergency_contact": "Guardian (9998887770)",
            "medical_history": "No known allergies"
        }
        success, msg, pid = PatientService.create_patient(test_patient)
        self.assertTrue(success, f"Create patient failed: {msg}")
        self.assertIsNotNone(pid)

        # 2. Search Patient
        results = PatientService.get_all_patients(search_term="Integration")
        self.assertTrue(any(p["patient_id"] == pid for p in results))

        # 3. Update Patient
        update_data = {
            "first_name": "Integration",
            "last_name": "Tester-Updated",
            "age": 36,
            "gender": "Female",
            "phone": "9998887776",
            "email": "integration.updated@hospital.org",
            "address": "101 QA Laboratory Lane",
            "blood_group": "AB+",
            "emergency_contact": "Guardian (9998887770)",
            "medical_history": "Seasonal pollen allergy"
        }
        up_success, up_msg = PatientService.update_patient(pid, update_data)
        self.assertTrue(up_success, f"Update failed: {up_msg}")

        # 4. Fetch History
        history = PatientService.get_patient_history(pid)
        self.assertEqual(history["patient"]["last_name"], "Tester-Updated")

        # 5. Delete Patient
        del_success, del_msg = PatientService.delete_patient(pid)
        self.assertTrue(del_success, f"Delete failed: {del_msg}")

    def test_03_doctor_crud_and_roster(self):
        """Tests doctor registration, filtering, schedule lookup, and deletion."""
        doc_data = {
            "first_name": "Neha",
            "last_name": "Bansal",
            "specialization": "Endocrinology",
            "department": "Internal Medicine",
            "phone": "9812345678",
            "email": "neha.b@hospital.org",
            "qualification": "MD, DM (Endocrinology)",
            "consultation_fee": 650.00,
            "available_days": "Mon,Wed,Fri",
            "shift_time": "10:00 AM - 03:00 PM",
            "status": "Active"
        }
        success, msg, doc_id = DoctorService.create_doctor(doc_data)
        self.assertTrue(success, f"Create doctor failed: {msg}")

        # Retrieve and filter
        docs = DoctorService.get_all_doctors(search_term="Bansal")
        self.assertTrue(any(d["doctor_id"] == doc_id for d in docs))

        # Delete doctor
        del_success, del_msg = DoctorService.delete_doctor(doc_id)
        self.assertTrue(del_success, f"Delete doctor failed: {del_msg}")

    def test_04_appointment_double_booking_prevention(self):
        """Tests appointment scheduling and strict prevention of doctor/patient double-booking."""
        # Use existing seeded Patient 1 and Doctor 1
        future_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        slot_time = "15:00:00"

        # 1. Schedule first appointment
        app1 = {
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_date": future_date,
            "appointment_time": slot_time,
            "reason": "Integration Test Booking 1"
        }
        s1, m1, id1 = AppointmentService.schedule_appointment(app1)
        self.assertTrue(s1, f"Initial booking failed: {m1}")

        # 2. Attempt double booking for same DOCTOR at same date/time with Patient 2 -> MUST FAIL
        app2 = {
            "patient_id": 2,
            "doctor_id": 1,
            "appointment_date": future_date,
            "appointment_time": slot_time,
            "reason": "Conflicting Booking (Doctor collision)"
        }
        s2, m2, _ = AppointmentService.schedule_appointment(app2)
        self.assertFalse(s2, "Doctor double-booking was NOT blocked!")
        self.assertIn("Conflict", m2)

        # 3. Attempt double booking for same PATIENT at same date/time with Doctor 2 -> MUST FAIL
        app3 = {
            "patient_id": 1,
            "doctor_id": 2,
            "appointment_date": future_date,
            "appointment_time": slot_time,
            "reason": "Conflicting Booking (Patient collision)"
        }
        s3, m3, _ = AppointmentService.schedule_appointment(app3)
        self.assertFalse(s3, "Patient double-booking was NOT blocked!")
        self.assertIn("Conflict", m3)

        # 4. Clean up test appointment
        AppointmentService.update_status(id1, "Cancelled", "Integration test cleanup")

    def test_05_bed_allocation_and_double_allocation_prevention(self):
        """Tests bed creation, allocation, double-allocation prevention, and releasing."""
        bed_data = {
            "bed_number": "TEST-B99",
            "ward_name": "Test Quarantine Ward",
            "bed_type": "Private",
            "daily_charge": 1500.00,
            "status": "Available",
            "notes": "Testing unit"
        }
        s, m, bed_id = BedService.create_bed(bed_data)
        self.assertTrue(s, f"Create bed failed: {m}")

        # Allocate bed -> should succeed
        s_alloc, m_alloc = BedService.allocate_bed(bed_id)
        self.assertTrue(s_alloc, f"Allocation failed: {m_alloc}")

        # Attempt to allocate ALREADY OCCUPIED bed -> MUST FAIL (Anti-double allocation)
        s_double, m_double = BedService.allocate_bed(bed_id)
        self.assertFalse(s_double, "Double-allocation of bed was NOT prevented!")

        # Release bed back to Available
        s_rel, m_rel = BedService.release_bed(bed_id)
        self.assertTrue(s_rel, f"Release failed: {m_rel}")

        # Delete test bed
        BedService.delete_bed(bed_id)

    def test_06_inpatient_admission_and_automated_discharge_release(self):
        """Tests admitting a patient (locks bed) and discharging (automatically releases bed)."""
        # Find an available bed
        available_beds = BedService.get_available_beds()
        self.assertGreater(len(available_beds), 0, "No available beds found for integration test")
        target_bed = available_beds[0]
        bed_id = target_bed["bed_id"]

        # Admit Patient 5
        adm_data = {
            "patient_id": 5,
            "bed_id": bed_id,
            "doctor_id": 1,
            "diagnosis": "Integration Test Pneumonia Protocol",
            "admission_type": "Urgent",
            "total_amount": 2500.00
        }
        s_adm, m_adm, adm_id = AdmissionService.admit_patient(adm_data)
        self.assertTrue(s_adm, f"Admission failed: {m_adm}")

        # Verify bed is now OCCUPIED
        bed_after_adm = BedService.get_bed_by_id(bed_id)
        self.assertEqual(bed_after_adm["status"], "Occupied")

        # Discharge patient -> Bed must automatically become AVAILABLE
        s_dis, m_dis = AdmissionService.discharge_patient(
            admission_id=adm_id,
            discharge_summary="Patient fully stabilized. Discharged home.",
            total_amount=3200.00
        )
        self.assertTrue(s_dis, f"Discharge failed: {m_dis}")

        bed_after_dis = BedService.get_bed_by_id(bed_id)
        self.assertEqual(bed_after_dis["status"], "Available", "Bed was NOT automatically released upon discharge!")

    def test_07_emergency_triage_priority_queue(self):
        """Tests emergency registration, heapq ordering (Critical > High > Med > Low), and triage dispatch."""
        case_low = {
            "patient_name": "Test Low Severity",
            "age": 22,
            "gender": "Female",
            "triage_severity": "Low",
            "chief_complaint": "Minor ankle sprain"
        }
        case_crit = {
            "patient_name": "Test Critical Severity",
            "age": 55,
            "gender": "Male",
            "triage_severity": "Critical",
            "chief_complaint": "Massive acute MI"
        }
        # Register Low first, then Critical
        s_low, _, id_low = EmergencyService.register_case(case_low)
        s_crit, _, id_crit = EmergencyService.register_case(case_crit)

        self.assertTrue(s_low and s_crit)

        # Check that Critical is top of queue
        top = EmergencyService.get_next_patient_to_treat()
        self.assertEqual(top["triage_severity"], "Critical", "Critical emergency was NOT prioritized over Low!")

        # Process Critical case
        s_proc, _ = EmergencyService.process_case(id_crit, "Treated", "Administered thrombolytics")
        self.assertTrue(s_proc)

        # Clean up low case
        EmergencyService.process_case(id_low, "Treated", "Applied crepe bandage")

    def test_08_dashboard_live_kpis(self):
        """Tests that live MySQL dashboard metrics are calculated accurately."""
        metrics = DashboardService.get_live_metrics()
        self.assertGreater(metrics["total_patients"], 0)
        self.assertGreater(metrics["total_doctors"], 0)
        self.assertGreater(metrics["total_beds"], 0)
        self.assertIn("bed_occupancy_pct", metrics)
        self.assertGreaterEqual(metrics["bed_occupancy_pct"], 0.0)

    def test_09_analytics_dataframes(self):
        """Tests Pandas aggregation services."""
        df_docs = AnalyticsService.get_doctor_workload_stats()
        self.assertFalse(df_docs.empty)
        self.assertIn("doctor_name", df_docs.columns)

        df_status = AnalyticsService.get_appointment_status_distribution()
        self.assertFalse(df_status.empty)

        df_beds = AnalyticsService.get_bed_occupancy_by_ward()
        self.assertFalse(df_beds.empty)

        df_emg = AnalyticsService.get_emergency_severity_stats()
        self.assertFalse(df_emg.empty)

    def test_10_reports_and_csv_export(self):
        """Tests tabular report generation and disk export."""
        headers, data = ReportService.get_patient_report()
        self.assertGreater(len(headers), 0)
        self.assertGreater(len(data), 0)

        succ, path = ReportService.export_to_csv(headers, data, filename_prefix="integration_test")
        self.assertTrue(succ)
        self.assertTrue(os.path.isfile(path))

        # Cleanup
        try:
            os.remove(path)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main()
