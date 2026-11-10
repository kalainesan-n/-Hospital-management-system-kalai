"""
Report Generation and CSV Export Service.
Generates comprehensive tabular reports across all modules with date range filtering
and export capabilities to CSV.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from database.connection import Database
import config

class ReportService:
    """Provides querying and CSV export routines for hospital audit and operational reports."""

    EXPORT_DIR = config.BASE_DIR / "reports_export"

    @classmethod
    def ensure_export_dir(cls) -> Path:
        """Ensures that the output directory for exported CSV files exists."""
        cls.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.EXPORT_DIR

    @classmethod
    def get_patient_report(cls, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[List[str], List[List[Any]]]:
        """Generates patient master report."""
        with Database() as db:
            conditions = []
            params = []
            if start_date:
                conditions.append("DATE(created_at) >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(created_at) <= %s")
                params.append(end_date)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT patient_code, first_name, last_name, date_of_birth, age, gender,
                       phone, email, blood_group, emergency_contact, created_at
                FROM patients
                {where}
                ORDER BY patient_id DESC
            """
            rows = db.execute_query(query, tuple(params))
            headers = ["Patient Code", "First Name", "Last Name", "DOB", "Age", "Gender", "Phone", "Email", "Blood Group", "Emergency Contact", "Registered At"]
            data = [[r['patient_code'], r['first_name'], r['last_name'], str(r['date_of_birth']), r['age'], r['gender'], r['phone'], r['email'] or '', r['blood_group'] or '', r['emergency_contact'] or '', str(r['created_at'])] for r in rows]
            return headers, data

    @classmethod
    def get_doctor_report(cls) -> Tuple[List[str], List[List[Any]]]:
        """Generates doctor registry report."""
        with Database() as db:
            query = """
                SELECT doctor_code, first_name, last_name, specialization, department,
                       phone, email, qualification, consultation_fee, shift_time, status
                FROM doctors
                ORDER BY doctor_id ASC
            """
            rows = db.execute_query(query)
            headers = ["Doctor Code", "First Name", "Last Name", "Specialization", "Department", "Phone", "Email", "Qualification", "Consultation Fee ($)", "Shift Time", "Status"]
            data = [[r['doctor_code'], r['first_name'], r['last_name'], r['specialization'], r['department'], r['phone'], r['email'], r['qualification'] or '', float(r['consultation_fee'] or 0), r['shift_time'], r['status']] for r in rows]
            return headers, data

    @classmethod
    def get_appointment_report(cls, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[str], List[List[Any]]]:
        """Generates appointment schedule and outcomes report."""
        with Database() as db:
            conditions = []
            params = []
            if start_date:
                conditions.append("a.appointment_date >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("a.appointment_date <= %s")
                params.append(end_date)
            if status and status != "All":
                conditions.append("a.status = %s")
                params.append(status)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT a.appointment_code, a.appointment_date, a.appointment_time, a.status,
                       p.patient_code, CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                       d.department, a.reason, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.patient_id
                JOIN doctors d ON a.doctor_id = d.doctor_id
                {where}
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
            rows = db.execute_query(query, tuple(params))
            headers = ["App Code", "Date", "Time", "Status", "Patient Code", "Patient Name", "Doctor Name", "Department", "Reason", "Clinical Notes"]
            data = [[r['appointment_code'], str(r['appointment_date']), str(r['appointment_time']), r['status'], r['patient_code'], r['patient_name'], r['doctor_name'], r['department'], r['reason'] or '', r['notes'] or ''] for r in rows]
            return headers, data

    @classmethod
    def get_bed_occupancy_report(cls) -> Tuple[List[str], List[List[Any]]]:
        """Generates bed inventory and status report."""
        with Database() as db:
            query = """
                SELECT bed_number, ward_name, bed_type, daily_charge, status, notes
                FROM beds
                ORDER BY ward_name ASC, bed_number ASC
            """
            rows = db.execute_query(query)
            headers = ["Bed Number", "Ward Name", "Bed Type", "Daily Charge ($)", "Status", "Facility Notes"]
            data = [[r['bed_number'], r['ward_name'], r['bed_type'], float(r['daily_charge'] or 0), r['status'], r['notes'] or ''] for r in rows]
            return headers, data

    @classmethod
    def get_admission_report(cls, start_date: Optional[str] = None, end_date: Optional[str] = None, status: Optional[str] = None) -> Tuple[List[str], List[List[Any]]]:
        """Generates in-patient admission and discharge audit report."""
        with Database() as db:
            conditions = []
            params = []
            if start_date:
                conditions.append("DATE(adm.admission_date) >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(adm.admission_date) <= %s")
                params.append(end_date)
            if status and status != "All":
                conditions.append("adm.status = %s")
                params.append(status)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT adm.admission_code, adm.admission_date, adm.discharge_date, adm.status,
                       adm.admission_type, adm.diagnosis, adm.total_amount,
                       p.patient_code, CONCAT(p.first_name, ' ', p.last_name) as patient_name,
                       b.bed_number, b.ward_name,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM admissions adm
                JOIN patients p ON adm.patient_id = p.patient_id
                JOIN beds b ON adm.bed_id = b.bed_id
                JOIN doctors d ON adm.doctor_id = d.doctor_id
                {where}
                ORDER BY adm.admission_date DESC
            """
            rows = db.execute_query(query, tuple(params))
            headers = ["Adm Code", "Admission Date", "Discharge Date", "Status", "Type", "Diagnosis", "Total ($)", "Patient Code", "Patient Name", "Bed", "Ward", "Attending Doctor"]
            data = [[r['admission_code'], str(r['admission_date']), str(r['discharge_date'] or '-'), r['status'], r['admission_type'], r['diagnosis'], float(r['total_amount'] or 0), r['patient_code'], r['patient_name'], r['bed_number'], r['ward_name'], r['doctor_name']] for r in rows]
            return headers, data

    @classmethod
    def get_emergency_report(cls, start_date: Optional[str] = None, end_date: Optional[str] = None, severity: Optional[str] = None) -> Tuple[List[str], List[List[Any]]]:
        """Generates emergency triage log report."""
        with Database() as db:
            conditions = []
            params = []
            if start_date:
                conditions.append("DATE(e.registered_at) >= %s")
                params.append(start_date)
            if end_date:
                conditions.append("DATE(e.registered_at) <= %s")
                params.append(end_date)
            if severity and severity != "All":
                conditions.append("e.triage_severity = %s")
                params.append(severity)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            query = f"""
                SELECT e.case_code, e.patient_name, e.age, e.gender, e.triage_severity,
                       e.priority_score, e.chief_complaint, e.status, e.registered_at, e.treated_at,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM emergency_cases e
                LEFT JOIN doctors d ON e.assigned_doctor_id = d.doctor_id
                {where}
                ORDER BY e.registered_at DESC
            """
            rows = db.execute_query(query, tuple(params))
            headers = ["Case Code", "Patient Name", "Age", "Gender", "Severity", "Score", "Chief Complaint", "Status", "Registered At", "Treated At", "Assigned Doctor"]
            data = [[r['case_code'], r['patient_name'], r['age'], r['gender'], r['triage_severity'], r['priority_score'], r['chief_complaint'], r['status'], str(r['registered_at']), str(r['treated_at'] or '-'), r['doctor_name'] or 'Unassigned'] for r in rows]
            return headers, data

    @classmethod
    def export_to_csv(cls, headers: List[str], data: List[List[Any]], filename_prefix: str = "report") -> Tuple[bool, str]:
        """Writes given tabular rows and headers to a timestamped CSV file."""
        try:
            out_dir = cls.ensure_export_dir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.csv"
            filepath = out_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data)

            return True, str(filepath)
        except Exception as e:
            return False, f"Export failed: {str(e)}"
