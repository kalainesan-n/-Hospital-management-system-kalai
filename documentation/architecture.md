# System Architecture & Technical Design

## 1. Architectural Overview

The **Intelligent Hospital Management and Analytics System** is built using a clean **Modular Layered Architecture** adhering to Separation of Concerns (SoC) principles:

```
+-------------------------------------------------------------------+
|                        PRESENTATION LAYER                         |
|   Tkinter + ttk Custom Dark Theme (`clam`) Engine                 |
|   - Reusable Components: StatCard, StyledTreeview, ModalDialog    |
|   - Modular Views: Dashboard, Patients, Doctors, Appointments,    |
|     Beds, Admissions, Emergency Triage, Analytics, Reports        |
|   - Embedded Matplotlib Canvas (FigureCanvasTkAgg)                |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                       BUSINESS LOGIC LAYER                        |
|   - AuthService (PBKDF2-HMAC-SHA256 Salted Hashing & Sessions)    |
|   - PatientService (CRUD, Profile History & Constraint Checks)    |
|   - DoctorService (Specialization Roster & Workload Scheduling)   |
|   - AppointmentService (Anti-Double-Booking Conflict Engine)      |
|   - BedService (Ward Capacity & Atomic Double-Allocation Lock)    |
|   - AdmissionService (Inpatient Lifecycle & Bed Release Trigger)  |
|   - EmergencyService (Min-Heap Priority Queue & Triage Dispatch)  |
|   - DashboardService (Live MySQL Aggregated Metrics)              |
|   - AnalyticsService (Pandas & NumPy Statistical Processing)      |
|   - ReportService (Audit Query Engine & CSV Exporters)            |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                          DATA ACCESS LAYER                        |
|   - Context-Managed Database Utility (`Database`)                 |
|   - Parameterized SQL Prepared Queries (Anti-SQLi)                |
|   - ACID Transactions with Atomic Commit / Rollback               |
|   - Schema Migration & Synthetic Demo Seeder (`init_db.py`)       |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                          PERSISTENCE LAYER                        |
|   MySQL 8.0+ Enterprise Relational Database                       |
|   - Tables: admins, patients, doctors, appointments, beds,        |
|             admissions, emergency_cases, activity_logs            |
+-------------------------------------------------------------------+
```

## 2. Directory Structure

```
├── main.py                     # Desktop application entry point & root window manager
├── config.py                   # Environment configuration loader (.env) & UI theme palette
├── requirements.txt            # System dependencies
├── README.md                   # Comprehensive project setup and usage guide
├── PROGRESS.md                 # Real-time implementation milestones
├── .env.example                # Sample database credentials configuration template
├── .gitignore                  # Protection against credential leaks & caches
│
├── frontend/                   # UI Presentation Layer
│   ├── __init__.py
│   ├── theme.py                # Modern Slate Dark Theme & ttk styles
│   ├── components.py           # Reusable widgets (StatCard, HeaderBar, SearchBar, StyledTreeview, ModalDialog)
│   ├── main_window.py          # Persistent sidebar navigation shell and view switcher
│   └── views/                  # Screen View Implementations
│       ├── __init__.py
│       ├── login_view.py       # Administrative authentication screen
│       ├── dashboard_view.py   # Live MySQL KPIs, today's schedule & audit stream
│       ├── patients_view.py    # Patient registry, search, CRUD & medical history dialog
│       ├── doctors_view.py     # Specialist roster, department filters & appointment schedule
│       ├── appointments_view.py# Conflict-preventing booking & status transitions
│       ├── beds_view.py        # Ward capacity monitoring & bed management
│       ├── admissions_view.py  # Inpatient hospitalization & automatic bed releasing
│       ├── emergency_view.py   # Educational Priority Queue & triage treatment dispatch
│       ├── analytics_view.py   # Embedded Matplotlib figures with Pandas aggregations
│       └── reports_view.py     # Filterable audit reports with CSV file export
│
├── backend/                    # Business Logic Layer
│   ├── __init__.py
│   ├── auth_service.py         # Salted PBKDF2 hashing & session tracking
│   ├── patient_service.py      # Patient operations & historical visit queries
│   ├── doctor_service.py       # Doctor profiles & availability tracking
│   ├── appointment_service.py  # Anti-double-booking conflict detection algorithms
│   ├── bed_service.py          # Ward occupancy & allocation locking
│   ├── admission_service.py    # Transactional admission & bed release routines
│   ├── emergency_service.py    # Python heapq Min-Heap Priority Queue
│   ├── dashboard_service.py    # Aggregate operational calculations
│   ├── analytics_service.py    # Pandas DataFrames & statistical transforms
│   └── report_service.py       # Tabular data generation & CSV export
│
├── database/                   # Data Access & Persistence
│   ├── __init__.py
│   ├── connection.py           # Context manager, transaction rollback, and parameterized queries
│   ├── schema.sql              # Relational MySQL DDL definitions & foreign keys
│   └── init_db.py              # Schema migration & rich synthetic demonstration seeder
│
├── tests/                      # Automated Unit Test Suite
│   ├── __init__.py
│   ├── test_priority_queue.py  # Min-Heap ordering and FIFO tie-break verification
│   ├── test_auth.py            # Password hashing & verification verification
│   └── test_services.py        # Reporting format & triage score mapping verification
│
└── documentation/              # Technical & Academic Documentation
    ├── architecture.md         # System design and component diagrams
    ├── database_design.md      # Relational schema reference and normalization
    ├── algorithms.md           # Algorithmic time complexity and conflict detection logic
    ├── testing_guide.md        # Quality assurance & verification manual
    └── viva_questions.md       # College viva voce defense guide & questions
```

## 3. Key Design Decisions

1. **Pure Desktop Architecture**: Built purely with standard Python, Tkinter, ttk, and MySQL. No web frameworks, webviews, or browser dependencies.
2. **Atomic Inpatient Bed Allocation**: Bed allocation and release are tied to admissions via atomic MySQL transactions, preventing double-allocation and orphaned bed states.
3. **Double-Booking Prevention**: Checks both doctor and patient schedules simultaneously to prevent booking overlaps.
4. **Educational Priority Queue**: Implements an in-memory `heapq` priority queue with an arrival sequence counter to ensure strict FIFO tie-breaking for equal priority scores. Prominently labeled with an academic disclaimer.
5. **Security First**: Passwords are never stored in plaintext. They are protected using PBKDF2-HMAC-SHA256 with 100,000 rounds and cryptographically unique salts. Database credentials are read from `.env` and kept out of version control.
