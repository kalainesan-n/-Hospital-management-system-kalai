-- =====================================================================
-- Intelligent Hospital Management and Analytics System
-- Database Schema Definition (MySQL)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS hospital_management_system
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hospital_management_system;

-- 1. Admin Users Table
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'Administrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_code VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    age INT,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    address TEXT,
    blood_group VARCHAR(5),
    emergency_contact VARCHAR(100),
    medical_history TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient_name (first_name, last_name),
    INDEX idx_patient_phone (phone)
) ENGINE=InnoDB;

-- 3. Doctors Table
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_code VARCHAR(20) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL,
    qualification VARCHAR(100),
    consultation_fee DECIMAL(10,2) DEFAULT 500.00,
    available_days VARCHAR(100) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    shift_time VARCHAR(50) DEFAULT '09:00 AM - 05:00 PM',
    status ENUM('Active', 'On Leave', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_doctor_dept (department),
    INDEX idx_doctor_specialization (specialization)
) ENGINE=InnoDB;

-- 4. Beds Table
CREATE TABLE IF NOT EXISTS beds (
    bed_id INT AUTO_INCREMENT PRIMARY KEY,
    bed_number VARCHAR(20) NOT NULL UNIQUE,
    ward_name VARCHAR(50) NOT NULL,
    bed_type ENUM('General', 'Semi-Private', 'Private', 'ICU', 'Emergency') NOT NULL DEFAULT 'General',
    daily_charge DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    status ENUM('Available', 'Occupied', 'Maintenance') NOT NULL DEFAULT 'Available',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ward_status (ward_name, status)
) ENGINE=InnoDB;

-- 5. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_code VARCHAR(20) NOT NULL UNIQUE,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason TEXT,
    status ENUM('Scheduled', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_doc_datetime (doctor_id, appointment_date, appointment_time),
    INDEX idx_pat_datetime (patient_id, appointment_date, appointment_time),
    INDEX idx_app_status (status)
) ENGINE=InnoDB;

-- 6. Admissions Table
CREATE TABLE IF NOT EXISTS admissions (
    admission_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_code VARCHAR(20) NOT NULL UNIQUE,
    patient_id INT NOT NULL,
    bed_id INT NOT NULL,
    doctor_id INT NOT NULL,
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME NULL,
    diagnosis TEXT NOT NULL,
    admission_type ENUM('Routine', 'Emergency', 'Urgent') DEFAULT 'Routine',
    status ENUM('Admitted', 'Discharged') DEFAULT 'Admitted',
    discharge_summary TEXT,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (bed_id) REFERENCES beds(bed_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_adm_status (status)
) ENGINE=InnoDB;

-- 7. Emergency Cases Table
-- Academic demonstration triage system (not clinically validated)
CREATE TABLE IF NOT EXISTS emergency_cases (
    emergency_id INT AUTO_INCREMENT PRIMARY KEY,
    case_code VARCHAR(20) NOT NULL UNIQUE,
    patient_name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    triage_severity ENUM('Critical', 'High', 'Medium', 'Low') NOT NULL,
    priority_score INT NOT NULL,
    chief_complaint TEXT NOT NULL,
    vitals_summary VARCHAR(255),
    assigned_doctor_id INT NULL,
    status ENUM('Pending', 'In Progress', 'Treated', 'Admitted', 'Transferred') DEFAULT 'Pending',
    registered_at DATETIME NOT NULL,
    treated_at DATETIME NULL,
    notes TEXT,
    FOREIGN KEY (assigned_doctor_id) REFERENCES doctors(doctor_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_emerg_status_priority (status, priority_score)
) ENGINE=InnoDB;

-- 8. Activity Logs Table
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50),
    details TEXT,
    performed_by VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
