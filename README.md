# Intelligent Hospital Management and Analytics System

A comprehensive, production-grade desktop hospital management and intelligence system developed from scratch in **Python 3**, **Tkinter + ttk (Modern Dark Theme)**, and **MySQL**.

---

## 1. Key Features

- **Admin Authentication**: Multi-factor password hashing (PBKDF2-HMAC-SHA256 with unique cryptographic salts), active session management, and audit logging.
- **Patient Management**: Full CRUD operations, phone and code search, and integrated medical history showing past outpatient consultations and hospital admissions.
- **Doctor Management**: Specialist profiles, department allocation, consulting fees, schedule slots, and individual consultation rosters.
- **Appointment Scheduling**: Outpatient scheduling with **real-time double-booking prevention** for both doctors and patients.
- **Bed Management**: Ward inventory tracking (ICU, Emergency, General, Private), capacity monitoring, and atomic double-allocation protection.
- **Admission & Discharge**: Inpatient hospitalization with automatic bed allocation and **automated bed release upon patient discharge**.
- **Emergency Management & Triage**: Educational **Python Priority Queue (`heapq` Min-Heap)** organizing emergency cases by severity (Critical > High > Medium > Low) with strict FIFO tie-breaking.
- **Operational Dashboard**: Live MySQL KPIs for patients, doctors, bed occupancy rates, active hospitalizations, pending emergencies, and real-time audit logs.
- **Hospital Intelligence & Analytics**: Statistical aggregations powered by **Pandas & NumPy** rendered via embedded **Matplotlib** charts.
- **Reports & Exporting**: Audit-ready data tables with date range filtering and one-click **CSV export**.

---

## 2. Technology Stack

- **Application Language**: Python 3.11+
- **Desktop Graphical Interface**: Tkinter & ttk (`clam` engine with custom dark theme)
- **Primary Relational Database**: MySQL 8.0+ / MariaDB
- **Database Connector**: `mysql-connector-python`
- **Analytics & Data Processing**: Pandas & NumPy
- **Visual Charting Engine**: Matplotlib (embedded via `FigureCanvasTkAgg`)
- **Configuration Management**: `.env` via `python-dotenv`

---

## 3. Installation & Setup

### 3.1 Prerequisites
- Python 3.10 or higher.
- MySQL Server 8.0+ (running locally on port 3306).

### 3.2 Install Dependencies
Install all required libraries via pip:
```bash
pip install -r requirements.txt
```

### 3.3 Configure Database Credentials
Create a `.env` file in the root directory (or edit the included template):
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hospital_management_system
```

### 3.4 Initialize Database & Synthetic Demo Data
Run the automated schema creation and demonstration seeder:
```bash
python database/init_db.py
```
This automatically:
1. Creates the `hospital_management_system` database if it does not exist.
2. Creates all relational tables, foreign key constraints, and indexes.
3. Inserts default admin credentials and rich synthetic records for doctors, patients, beds, appointments, admissions, and emergency cases.

---

## 4. Running the Application

Launch the desktop system:
```bash
python main.py
```

### Default Administrative Credentials:
- **Username**: `admin`
- **Password**: `admin123`

---

## 5. Running Automated Tests

Run the full automated test suite:
```bash
python -m unittest discover tests -v
```

Or run individual tests:
```bash
python tests/test_priority_queue.py
python tests/test_auth.py
python tests/test_services.py
```

---

## 6. Project Architecture

```
├── main.py                     # Application Entry Point
├── config.py                   # Configuration and Dark Theme Settings
├── requirements.txt            # Python Dependencies
├── README.md                   # System Documentation
├── PROGRESS.md                 # Development Progress Log
│
├── frontend/                   # UI Presentation Layer
│   ├── theme.py                # Styling engine & dark color palette
│   ├── components.py           # Reusable UI widgets
│   ├── main_window.py          # Persistent sidebar navigation shell
│   └── views/                  # Screen modules (Dashboard, Patients, etc.)
│
├── backend/                    # Business Logic Layer
│   ├── auth_service.py         # Authentication & password hashing
│   ├── patient_service.py      # Patient operations & history
│   ├── doctor_service.py       # Doctor profiles & availability
│   ├── appointment_service.py  # Double-booking prevention algorithm
│   ├── bed_service.py          # Bed capacity & allocation logic
│   ├── admission_service.py    # Inpatient management & bed release
│   ├── emergency_service.py    # Priority queue triage algorithm
│   ├── dashboard_service.py    # Live MySQL statistics calculations
│   ├── analytics_service.py    # Pandas statistical processing
│   └── report_service.py       # CSV reporting engine
│
├── database/                   # Persistence Layer
│   ├── connection.py           # Database context manager & transactions
│   ├── schema.sql              # MySQL DDL schema definitions
│   └── init_db.py              # Automated schema setup & seeder
│
├── tests/                      # Automated Test Suite
│   ├── test_priority_queue.py  # Min-heap & FIFO verification
│   ├── test_auth.py            # Password hashing verification
│   └── test_services.py        # Service logic & export verification
│
└── documentation/              # Academic & Technical Guides
    ├── architecture.md         # System design diagrams
    ├── database_design.md      # Relational schema reference
    ├── algorithms.md           # Algorithmic time complexities
    ├── testing_guide.md        # QA verification guide
    └── viva_questions.md       # College viva voce defense guide
```
