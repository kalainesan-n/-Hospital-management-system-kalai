"""
Database initialization and synthetic demonstration data seeder.
Connects to MySQL, executes schema.sql, and inserts realistic demo records.
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
import mysql.connector

# Ensure root directory is on Python path
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from backend.auth_service import AuthService

def initialize_database():
    """Initializes the database schema and populates demonstration records."""
    print(f"Connecting to MySQL server at {config.DB_HOST}:{config.DB_PORT} as '{config.DB_USER}'...")

    try:
        # Step 1: Connect to server without database to create database if not exists
        server_conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        server_cursor = server_conn.cursor()
        server_cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        server_cursor.close()
        server_conn.close()
        print(f"Database '{config.DB_NAME}' verified/created.")

        # Step 2: Connect to the specific database and execute schema
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            port=config.DB_PORT
        )
        cursor = conn.cursor(dictionary=True)

        schema_file = CURRENT_DIR / 'schema.sql'
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Split SQL commands by semicolon (ignoring empty statements or comments)
        statements = []
        current_stmt = []
        for line in sql_script.splitlines():
            line_strip = line.strip()
            if not line_strip or line_strip.startswith('--') or line_strip.startswith('/*'):
                continue
            current_stmt.append(line)
            if line_strip.endswith(';'):
                statements.append("\n".join(current_stmt))
                current_stmt = []

        for stmt in statements:
            stmt_clean = stmt.strip()
            if stmt_clean:
                try:
                    cursor.execute(stmt_clean)
                except mysql.connector.Error as err:
                    # Ignore USE database errors or duplicate warnings
                    if "database changed" not in str(err).lower():
                        pass

        conn.commit()
        print("Schema tables and constraints created successfully.")

        # Step 3: Seed Admin User if not exists
        cursor.execute("SELECT COUNT(*) as count FROM admins WHERE username = 'admin'")
        if cursor.fetchone()['count'] == 0:
            salt = AuthService.generate_salt()
            pwd_hash, _ = AuthService.hash_password("admin123", salt)
            cursor.execute(
                """INSERT INTO admins (username, password_hash, salt, full_name, email, role)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                ("admin", pwd_hash, salt, "Chief Medical Administrator", "admin@hospital.org", "Super Admin")
            )
            print("Default admin user created: username='admin', password='admin123'")

        # Step 4: Seed Demonstration Doctors
        cursor.execute("SELECT COUNT(*) as count FROM doctors")
        if cursor.fetchone()['count'] == 0:
            doctors = [
                ("DOC-001", "Aarav", "Sharma", "Cardiology", "Cardiovascular Sciences", "9876543210", "aarav.sharma@hospital.org", "MD, DM (Cardiology)", 800.00, "Mon,Tue,Wed,Thu,Fri", "09:00 AM - 02:00 PM", "Active"),
                ("DOC-002", "Priya", "Nair", "Neurology", "Neurosciences", "9876543211", "priya.nair@hospital.org", "MBBS, MD, DM (Neurology)", 900.00, "Mon,Wed,Fri", "10:00 AM - 04:00 PM", "Active"),
                ("DOC-003", "Vikram", "Patel", "Orthopedics", "Bone & Joint Institute", "9876543212", "vikram.patel@hospital.org", "MS (Orthopedics), MCh", 750.00, "Tue,Thu,Sat", "09:00 AM - 01:00 PM", "Active"),
                ("DOC-004", "Ananya", "Deshmukh", "Pediatrics", "Child Health Care", "9876543213", "ananya.d@hospital.org", "MD (Pediatrics), DCH", 600.00, "Mon,Tue,Wed,Thu,Fri,Sat", "09:00 AM - 05:00 PM", "Active"),
                ("DOC-005", "Rohan", "Mehta", "General Surgery", "Surgical Department", "9876543214", "rohan.mehta@hospital.org", "MS, FRCS", 1000.00, "Mon,Tue,Thu", "08:00 AM - 02:00 PM", "Active"),
                ("DOC-006", "Kavita", "Iyer", "Internal Medicine", "General Medicine", "9876543215", "kavita.iyer@hospital.org", "MD (Internal Medicine)", 550.00, "Mon,Tue,Wed,Thu,Fri", "01:00 PM - 07:00 PM", "Active"),
            ]
            cursor.executemany(
                """INSERT INTO doctors (doctor_code, first_name, last_name, specialization, department, phone, email, qualification, consultation_fee, available_days, shift_time, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                doctors
            )
            print(f"Seeded {len(doctors)} doctors.")

        # Step 5: Seed Demonstration Beds
        cursor.execute("SELECT COUNT(*) as count FROM beds")
        if cursor.fetchone()['count'] == 0:
            beds = [
                ("ICU-101", "Intensive Care Unit", "ICU", 3500.00, "Available", "Equipped with advanced ventilator"),
                ("ICU-102", "Intensive Care Unit", "ICU", 3500.00, "Available", "Equipped with multi-para cardiac monitor"),
                ("ICU-103", "Intensive Care Unit", "ICU", 3500.00, "Available", "Cardiac ICU bed"),
                ("EMG-201", "Emergency Ward", "Emergency", 2000.00, "Available", "Rapid triage bed A"),
                ("EMG-202", "Emergency Ward", "Emergency", 2000.00, "Available", "Rapid triage bed B"),
                ("GEN-301", "General Ward A", "General", 600.00, "Available", "Standard motorized bed"),
                ("GEN-302", "General Ward A", "General", 600.00, "Available", "Standard motorized bed"),
                ("GEN-303", "General Ward A", "General", 600.00, "Available", "Standard motorized bed"),
                ("GEN-304", "General Ward B", "General", 600.00, "Available", "Standard motorized bed"),
                ("GEN-305", "General Ward B", "General", 600.00, "Available", "Standard motorized bed"),
                ("PVT-401", "Private Deluxe Wing", "Private", 1800.00, "Available", "Ensuite private room with sofa"),
                ("PVT-402", "Private Deluxe Wing", "Private", 1800.00, "Available", "Ensuite private room with TV"),
                ("SPV-501", "Semi-Private Ward", "Semi-Private", 1200.00, "Available", "Twin sharing cubicle 1"),
                ("SPV-502", "Semi-Private Ward", "Semi-Private", 1200.00, "Available", "Twin sharing cubicle 2"),
            ]
            cursor.executemany(
                """INSERT INTO beds (bed_number, ward_name, bed_type, daily_charge, status, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                beds
            )
            print(f"Seeded {len(beds)} hospital beds.")

        # Step 6: Seed Demonstration Patients
        cursor.execute("SELECT COUNT(*) as count FROM patients")
        if cursor.fetchone()['count'] == 0:
            patients = [
                ("PAT-001", "Rajesh", "Kumar", "1980-05-14", 46, "Male", "9811223344", "rajesh.k@gmail.com", "12 Park Avenue, Chennai", "O+", "Suman Kumar (9811223345)", "Hypertension, Mild Asthma"),
                ("PAT-002", "Sunita", "Reddy", "1992-09-21", 34, "Female", "9822334455", "sunita.r@gmail.com", "45 Lake Road, Hyderabad", "B+", "Venkat Reddy (9822334456)", "No major prior illnesses"),
                ("PAT-003", "Mohammed", "Arif", "1975-12-03", 51, "Male", "9833445566", "arif.m@gmail.com", "78 MG Road, Bengaluru", "A+", "Amina Arif (9833445567)", "Type 2 Diabetes Mellitus"),
                ("PAT-004", "Lakshmi", "Sundaram", "1968-03-30", 58, "Female", "9844556677", "lakshmi.s@gmail.com", "23 Gandhi Street, Madurai", "AB+", "Raman Sundaram (9844556678)", "Osteoarthritis, Hypothyroidism"),
                ("PAT-005", "David", "Wilson", "1998-07-19", 28, "Male", "9855667788", "david.w@gmail.com", "89 Church Street, Kochi", "O-", "Grace Wilson (9855667789)", "Dust allergy"),
                ("PAT-006", "Meera", "Sen", "2005-11-12", 21, "Female", "9866778899", "meera.sen@gmail.com", "54 Sarat Bose Road, Kolkata", "B-", "Debashis Sen (9866778800)", "Migraine"),
                ("PAT-007", "Karthik", "Subramanian", "1985-01-25", 41, "Male", "9877889900", "karthik.sub@gmail.com", "10 Anna Salai, Chennai", "A-", "Deepa Karthik (9877889901)", "Dyslipidemia"),
                ("PAT-008", "Deepika", "Chawla", "1990-08-16", 36, "Female", "9888990011", "deepika.c@gmail.com", "90 Civil Lines, Delhi", "O+", "Harsh Chawla (9888990012)", "None"),
            ]
            cursor.executemany(
                """INSERT INTO patients (patient_code, first_name, last_name, date_of_birth, age, gender, phone, email, address, blood_group, emergency_contact, medical_history)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                patients
            )
            print(f"Seeded {len(patients)} patients.")

        # Step 7: Seed Appointments (Recent past and today)
        cursor.execute("SELECT COUNT(*) as count FROM appointments")
        if cursor.fetchone()['count'] == 0:
            today_str = date.today().strftime("%Y-%m-%d")
            yesterday_str = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            tomorrow_str = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

            appointments = [
                ("APP-1001", 1, 1, today_str, "09:30:00", "Quarterly Cardiac Review", "Scheduled", "Patient advised to bring ECG reports."),
                ("APP-1002", 2, 2, today_str, "11:00:00", "Frequent migraine headaches", "Scheduled", "Review headache diary."),
                ("APP-1003", 3, 6, today_str, "14:00:00", "Diabetic routine checkup", "Scheduled", "Check Fasting blood sugar."),
                ("APP-1004", 4, 3, yesterday_str, "10:30:00", "Persistent knee pain", "Completed", "Prescribed pain relief and physiotherapy."),
                ("APP-1005", 5, 4, yesterday_str, "11:30:00", "General pediatric consultation", "Completed", "Child growth parameters normal."),
                ("APP-1006", 6, 2, tomorrow_str, "10:00:00", "Follow-up consultation", "Scheduled", "Review MRI scan."),
                ("APP-1007", 7, 5, yesterday_str, "12:00:00", "Hernia pre-op evaluation", "Cancelled", "Cancelled due to personal emergency."),
            ]
            cursor.executemany(
                """INSERT INTO appointments (appointment_code, patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                appointments
            )
            print(f"Seeded {len(appointments)} appointments.")

        # Step 8: Seed Admissions and mark corresponding beds as Occupied
        cursor.execute("SELECT COUNT(*) as count FROM admissions")
        if cursor.fetchone()['count'] == 0:
            now_dt = datetime.now()
            adm1_date = (now_dt - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
            adm2_date = (now_dt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            adm3_date = (now_dt - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            dis3_date = (now_dt - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

            # Active admission 1: Patient 1 in Bed 1 (ICU-101)
            cursor.execute(
                """INSERT INTO admissions (admission_code, patient_id, bed_id, doctor_id, admission_date, diagnosis, admission_type, status, total_amount)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                ("ADM-5001", 1, 1, 1, adm1_date, "Acute Coronary Syndrome", "Emergency", "Admitted", 12500.00)
            )
            cursor.execute("UPDATE beds SET status = 'Occupied' WHERE bed_id = 1")

            # Active admission 2: Patient 3 in Bed 6 (GEN-301)
            cursor.execute(
                """INSERT INTO admissions (admission_code, patient_id, bed_id, doctor_id, admission_date, diagnosis, admission_type, status, total_amount)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                ("ADM-5002", 3, 6, 6, adm2_date, "Diabetic Ketoacidosis management", "Urgent", "Admitted", 4800.00)
            )
            cursor.execute("UPDATE beds SET status = 'Occupied' WHERE bed_id = 6")

            # Completed admission 3: Patient 4 in Bed 11 (discharged)
            cursor.execute(
                """INSERT INTO admissions (admission_code, patient_id, bed_id, doctor_id, admission_date, discharge_date, diagnosis, admission_type, status, discharge_summary, total_amount)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                ("ADM-5003", 4, 11, 3, adm3_date, dis3_date, "Knee Arthroscopy", "Routine", "Discharged", "Patient recovered well. Suture removal in 10 days.", 8900.00)
            )
            print("Seeded admissions and updated corresponding bed statuses.")

        # Step 9: Seed Emergency Cases (for priority queue demonstration)
        cursor.execute("SELECT COUNT(*) as count FROM emergency_cases")
        if cursor.fetchone()['count'] == 0:
            now_dt = datetime.now()
            cases = [
                ("EMG-C01", "Ramesh Verma", 62, "Male", "Critical", 1, "Severe chest pain, diaphoresis, BP 80/50", "Pulse 120, BP 80/50, SpO2 88%", 1, "Pending", (now_dt - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")),
                ("EMG-C02", "Shalini Gupta", 29, "Female", "High", 2, "Compound fracture right tibia with active bleed", "Pulse 98, BP 110/70, SpO2 97%", 3, "Pending", (now_dt - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S")),
                ("EMG-C03", "Tarun Joshi", 45, "Male", "Medium", 3, "Acute abdominal pain with high grade fever", "Pulse 88, BP 125/82, Temp 102F", 5, "Pending", (now_dt - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M:%S")),
                ("EMG-C04", "Simran Kaur", 24, "Female", "Low", 4, "Superficial kitchen burn on left forearm", "Pulse 76, BP 118/76, SpO2 99%", 6, "Pending", (now_dt - timedelta(minutes=50)).strftime("%Y-%m-%d %H:%M:%S")),
                ("EMG-C05", "Abhishek Das", 50, "Male", "Critical", 1, "Acute respiratory distress, choking sensation", "Pulse 130, BP 145/95, SpO2 82%", 1, "In Progress", (now_dt - timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S")),
            ]
            cursor.executemany(
                """INSERT INTO emergency_cases (case_code, patient_name, age, gender, triage_severity, priority_score, chief_complaint, vitals_summary, assigned_doctor_id, status, registered_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                cases
            )
            print(f"Seeded {len(cases)} emergency cases.")

        # Step 10: Seed Activity Logs
        cursor.execute("SELECT COUNT(*) as count FROM activity_logs")
        if cursor.fetchone()['count'] == 0:
            logs = [
                ("SYSTEM_INIT", "Database", "ALL", "System database initialized with demonstrative baseline records.", "admin"),
                ("BED_ALLOCATED", "Bed", "ICU-101", "Bed allocated to admitted patient Rajesh Kumar.", "admin"),
                ("BED_ALLOCATED", "Bed", "GEN-301", "Bed allocated to admitted patient Mohammed Arif.", "admin"),
                ("EMERGENCY_TRIAGED", "Emergency", "EMG-C01", "Critical emergency registered: Ramesh Verma.", "admin"),
            ]
            cursor.executemany(
                """INSERT INTO activity_logs (action, entity_type, entity_id, details, performed_by)
                   VALUES (%s, %s, %s, %s, %s)""",
                logs
            )
            print("Seeded activity logs.")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialization and demonstration seeding completed successfully!")
        return True, "Database initialized and seeded successfully."

    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    success, msg = initialize_database()
    if not success:
        sys.exit(1)
