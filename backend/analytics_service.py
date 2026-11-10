"""
Analytics Service.
Leverages Pandas and NumPy to compute statistical aggregations, distributions,
and trend analyses from hospital operational data.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database.connection import Database

class AnalyticsService:
    """Processes historical and real-time records into statistical DataFrames."""

    @classmethod
    def get_patient_registration_stats(cls) -> pd.DataFrame:
        """Computes daily patient registration frequencies over the last 30 days."""
        with Database() as db:
            query = """
                SELECT DATE(created_at) as reg_date, COUNT(*) as count
                FROM patients
                GROUP BY DATE(created_at)
                ORDER BY reg_date ASC
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["reg_date", "count"])
            df = pd.DataFrame(rows)
            df['reg_date'] = pd.to_datetime(df['reg_date'])
            return df

    @classmethod
    def get_appointment_status_distribution(cls) -> pd.DataFrame:
        """Returns distribution of appointment statuses (Scheduled, Completed, Cancelled, No-Show)."""
        with Database() as db:
            query = """
                SELECT status, COUNT(*) as count
                FROM appointments
                GROUP BY status
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["status", "count"])
            return pd.DataFrame(rows)

    @classmethod
    def get_doctor_workload_stats(cls) -> pd.DataFrame:
        """Computes appointment counts per doctor and department."""
        with Database() as db:
            query = """
                SELECT 
                    CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name,
                    d.department,
                    d.specialization,
                    COUNT(a.appointment_id) as total_appointments,
                    SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) as completed_appointments
                FROM doctors d
                LEFT JOIN appointments a ON d.doctor_id = a.doctor_id
                GROUP BY d.doctor_id, doctor_name, d.department, d.specialization
                ORDER BY total_appointments DESC
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["doctor_name", "department", "specialization", "total_appointments", "completed_appointments"])
            return pd.DataFrame(rows)

    @classmethod
    def get_bed_occupancy_by_ward(cls) -> pd.DataFrame:
        """Computes total, occupied, and available beds grouped by ward."""
        with Database() as db:
            query = """
                SELECT 
                    ward_name,
                    SUM(CASE WHEN status = 'Occupied' THEN 1 ELSE 0 END) as occupied,
                    SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
                    SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance,
                    COUNT(*) as total
                FROM beds
                GROUP BY ward_name
                ORDER BY total DESC
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["ward_name", "occupied", "available", "maintenance", "total"])
            return pd.DataFrame(rows)

    @classmethod
    def get_emergency_severity_stats(cls) -> pd.DataFrame:
        """Computes frequency and processing metrics by emergency severity level."""
        with Database() as db:
            query = """
                SELECT 
                    triage_severity,
                    COUNT(*) as total_cases,
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_cases,
                    SUM(CASE WHEN status = 'Treated' THEN 1 ELSE 0 END) as treated_cases,
                    AVG(age) as average_patient_age
                FROM emergency_cases
                GROUP BY triage_severity
                ORDER BY FIELD(triage_severity, 'Critical', 'High', 'Medium', 'Low')
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["triage_severity", "total_cases", "pending_cases", "treated_cases", "average_patient_age"])
            df = pd.DataFrame(rows)
            df['average_patient_age'] = df['average_patient_age'].fillna(0).round(1)
            return df

    @classmethod
    def get_admission_discharge_comparison(cls) -> pd.DataFrame:
        """Computes admission types and discharge status distribution."""
        with Database() as db:
            query = """
                SELECT 
                    admission_type,
                    SUM(CASE WHEN status = 'Admitted' THEN 1 ELSE 0 END) as active_admissions,
                    SUM(CASE WHEN status = 'Discharged' THEN 1 ELSE 0 END) as discharged_cases,
                    AVG(total_amount) as avg_revenue
                FROM admissions
                GROUP BY admission_type
            """
            rows = db.execute_query(query)
            if not rows:
                return pd.DataFrame(columns=["admission_type", "active_admissions", "discharged_cases", "avg_revenue"])
            df = pd.DataFrame(rows)
            df['avg_revenue'] = df['avg_revenue'].fillna(0).round(2)
            return df
