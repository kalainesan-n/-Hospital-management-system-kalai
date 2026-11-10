# Relational Database Design Reference

## 1. Database Schema Specifications

- **Database Engine**: MySQL 8.0+ / MariaDB (InnoDB Storage Engine)
- **Character Set**: `utf8mb4`
- **Collation**: `utf8mb4_unicode_ci`

---

## 2. Entity-Relationship Model

```
       +--------------+
       |    Admins    |
       +--------------+

       +--------------+                   +--------------+
       |   Patients   |<-------+          |   Doctors    |<-------+
       +--------------+        |          +--------------+        |
              |                |                 |                |
              | 1              | 1               | 1              | 1
              |                |                 |                |
              v N              v N               v N              v N
       +--------------+  +--------------+  +--------------+  +-----------------+
       | Appointments |  |  Admissions  |  | Appointments |  | Emergency_Cases |
       +--------------+  +--------------+  +--------------+  +-----------------+
                               ^
                               | N
                               |
                               | 1
                         +--------------+
                         |     Beds     |
                         +--------------+
```

---

## 3. Table Definitions & Constraints

### 3.1 `admins`
Stores authenticated hospital administrative staff credentials.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `admin_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique identifier |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Administrative login ID |
| `password_hash` | VARCHAR(255) | NOT NULL | PBKDF2-HMAC-SHA256 hash |
| `salt` | VARCHAR(64) | NOT NULL | 32-character hexadecimal salt |
| `full_name` | VARCHAR(100) | NOT NULL | Administrator's display name |
| `email` | VARCHAR(100) | NOT NULL | Contact email address |
| `role` | VARCHAR(50) | DEFAULT 'Administrator' | Permission tier |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record registration timestamp |

---

### 3.2 `patients`
Central registry of registered outpatients and inpatients.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `patient_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique internal key |
| `patient_code` | VARCHAR(20) | UNIQUE, NOT NULL | Formatted hospital ID (e.g. `PAT-0001`) |
| `first_name` | VARCHAR(50) | NOT NULL | Patient given name |
| `last_name` | VARCHAR(50) | NOT NULL | Patient surname |
| `date_of_birth`| DATE | NULL | Date of birth |
| `age` | INT | NULL | Computed / recorded age |
| `gender` | ENUM | NOT NULL ('Male','Female','Other') | Biological / demographic gender |
| `phone` | VARCHAR(20) | NOT NULL | Contact telephone |
| `email` | VARCHAR(100) | NULL | Communication email |
| `address` | TEXT | NULL | Physical residence |
| `blood_group` | VARCHAR(5) | NULL | ABO blood type |
| `emergency_contact` | VARCHAR(100) | NULL | Kin contact details |
| `medical_history`| TEXT | NULL | Known allergies and chronic conditions |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

**Indexes**: `idx_patient_name (first_name, last_name)`, `idx_patient_phone (phone)`

---

### 3.3 `doctors`
Medical consultants, surgeons, and specialists.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `doctor_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique internal identifier |
| `doctor_code` | VARCHAR(20) | UNIQUE, NOT NULL | Physician code (e.g. `DOC-001`) |
| `first_name` | VARCHAR(50) | NOT NULL | Physician first name |
| `last_name` | VARCHAR(50) | NOT NULL | Physician last name |
| `specialization`| VARCHAR(100)| NOT NULL | Clinical subspecialty |
| `department` | VARCHAR(100)| NOT NULL | Hospital department |
| `phone` | VARCHAR(20) | NOT NULL | Mobile / bleep number |
| `email` | VARCHAR(100)| NOT NULL | Professional email |
| `qualification`| VARCHAR(100)| NULL | Degree credentials (MD, MS, DM) |
| `consultation_fee`| DECIMAL(10,2)| DEFAULT 500.00 | Fee per outpatient consultation |
| `available_days`| VARCHAR(100)| DEFAULT 'Mon,Tue,Wed,Thu,Fri' | Clinic operating days |
| `shift_time` | VARCHAR(50) | DEFAULT '09:00 AM - 05:00 PM' | Standard shift duration |
| `status` | ENUM | 'Active', 'On Leave', 'Inactive' | Roster availability status |

**Indexes**: `idx_doctor_dept (department)`, `idx_doctor_specialization (specialization)`

---

### 3.4 `beds`
Hospital bed inventory across wards and specialty units.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `bed_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique bed identifier |
| `bed_number` | VARCHAR(20) | UNIQUE, NOT NULL | Physical bed tag (e.g. `ICU-101`) |
| `ward_name` | VARCHAR(50) | NOT NULL | Hospital ward location |
| `bed_type` | ENUM | 'General','Semi-Private','Private','ICU','Emergency' | Ward classification |
| `daily_charge` | DECIMAL(10,2)| NOT NULL DEFAULT 500.00 | Daily hospitalization rate |
| `status` | ENUM | 'Available','Occupied','Maintenance' | Current bed occupancy state |
| `notes` | TEXT | NULL | Equipment and facility notes |

**Indexes**: `idx_ward_status (ward_name, status)`

---

### 3.5 `appointments`
Outpatient bookings and consultation records.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `appointment_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique appointment ID |
| `appointment_code`| VARCHAR(20)| UNIQUE, NOT NULL | Tracking code (e.g. `APP-1001`) |
| `patient_id` | INT | FK -> `patients(patient_id)` | Scheduled patient |
| `doctor_id` | INT | FK -> `doctors(doctor_id)` | Consulting physician |
| `appointment_date`| DATE | NOT NULL | Consultation calendar date |
| `appointment_time`| TIME | NOT NULL | Consultation slot time |
| `reason` | TEXT | NULL | Chief complaint / purpose of visit |
| `status` | ENUM | 'Scheduled','Completed','Cancelled','No-Show' | Lifecycle state |
| `notes` | TEXT | NULL | Doctor clinical consultation notes |

**Indexes**: `idx_doc_datetime (doctor_id, appointment_date, appointment_time)`, `idx_pat_datetime (patient_id, appointment_date, appointment_time)`, `idx_app_status (status)`

---

### 3.6 `admissions`
Inpatient hospitalizations linking patients, beds, and attending doctors.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `admission_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique hospitalization key |
| `admission_code` | VARCHAR(20) | UNIQUE, NOT NULL | Admission record code (e.g. `ADM-5001`)|
| `patient_id` | INT | FK -> `patients(patient_id)` | Admitted patient |
| `bed_id` | INT | FK -> `beds(bed_id)` | Assigned hospital bed |
| `doctor_id` | INT | FK -> `doctors(doctor_id)` | Primary attending doctor |
| `admission_date` | DATETIME | NOT NULL | Intake timestamp |
| `discharge_date` | DATETIME | NULL | Discharge timestamp |
| `diagnosis` | TEXT | NOT NULL | Admission clinical diagnosis |
| `admission_type` | ENUM | 'Routine','Emergency','Urgent' | Admission category |
| `status` | ENUM | 'Admitted','Discharged' | Current inpatient state |
| `discharge_summary`| TEXT | NULL | Final medical discharge notes |
| `total_amount` | DECIMAL(10,2)| DEFAULT 0.00 | Accumulated inpatient bill |

---

### 3.7 `emergency_cases`
Emergency triage cases prioritized via Min-Heap algorithm.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `emergency_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Unique emergency case ID |
| `case_code` | VARCHAR(20) | UNIQUE, NOT NULL | Intake code (e.g. `EMG-C01`) |
| `patient_name` | VARCHAR(100)| NOT NULL | Emergency patient full name |
| `age` | INT | NOT NULL | Patient age |
| `gender` | ENUM | 'Male','Female','Other' | Gender |
| `triage_severity`| ENUM | 'Critical','High','Medium','Low' | Clinical triage classification |
| `priority_score` | INT | NOT NULL (1 to 4) | Min-Heap priority integer |
| `chief_complaint`| TEXT | NOT NULL | Acute symptom presentation |
| `vitals_summary` | VARCHAR(255)| NULL | BP, Pulse, SpO2, Temperature |
| `assigned_doctor_id`| INT | NULL, FK -> `doctors(doctor_id)` | Attending emergency physician |
| `status` | ENUM | 'Pending','In Progress','Treated','Admitted','Transferred' | Clinical status |
| `registered_at` | DATETIME | NOT NULL | Emergency arrival timestamp |
| `treated_at` | DATETIME | NULL | Treatment initiation timestamp |

---

### 3.8 `activity_logs`
System-wide audit trail for all write operations.
| Column | Type | Constraints | Description |
|---|---|---|---|
| `log_id` | INT | PRIMARY KEY, AUTO_INCREMENT | Audit log sequence number |
| `action` | VARCHAR(100) | NOT NULL | Event type (e.g. `BED_ALLOCATED`) |
| `entity_type` | VARCHAR(50) | NOT NULL | Target entity (e.g. `Bed`, `Patient`) |
| `entity_id` | VARCHAR(50) | NULL | Record reference code |
| `details` | TEXT | NULL | Contextual description |
| `performed_by`| VARCHAR(50) | DEFAULT 'admin' | User session identifier |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Log generation timestamp |

---

## 4. Normalization Standards

The database is normalized to **Third Normal Form (3NF)**:
1. **1NF**: All table columns are atomic and contain no repeating groups.
2. **2NF**: All non-key attributes are fully functionally dependent on the primary key.
3. **3NF**: There are no transitive dependencies; non-key columns depend only on primary keys.
