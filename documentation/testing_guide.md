# Automated Testing and Quality Assurance Guide

## 1. Automated Test Suite Execution

The application comes with comprehensive automated unit, integration, and GUI test suites covering the core algorithmic, cryptographic, database, and presentation modules.

To execute the complete test suite from the project root:

```bash
python -m unittest discover tests -v
```

Or execute individual test suites:

```bash
# 1. Full End-to-End Live MySQL Integration Test Suite
python -m unittest tests/test_integration.py -v

# 2. GUI Smoke & Navigation Lifecycle Test
python -m unittest tests/test_gui.py -v

# 3. Test Priority Queue (Min-Heap and FIFO tie-breaking)
python tests/test_priority_queue.py

# 4. Test Authentication & Password Hashing (PBKDF2-HMAC-SHA256)
python tests/test_auth.py

# 5. Test Service Layer Helpers & CSV Exporters
python tests/test_services.py
```

---

## 2. Test Coverage & Results Summary

| Test Module | Coverage Scope | Result | Status |
|---|---|---|---|
| `test_integration.py` | Full live MySQL database integration: Admin login, Patient CRUD, Doctor CRUD, Appointment scheduling, Anti-double-booking conflict detection, Bed allocation & anti-double-allocation locking, Inpatient admission & automated bed release on discharge, Emergency triage priority queue, Dashboard calculations, Analytics DataFrames, CSV report generation | 10 / 10 | **PASSED** |
| `test_gui.py` | Tkinter root lifecycle, dark theme application, login screen rendering, credential submission, main window instantiation, and seamless cycling across all 9 views with Matplotlib canvas drawing | 1 / 1 | **PASSED** |
| `test_priority_queue.py` | Min-Heap priority sorting (Critical > High > Medium > Low), FIFO arrival tie-breaking for equal severity scores, non-destructive peek, clear | 4 / 4 | **PASSED** |
| `test_auth.py` | Salt generation uniqueness, PBKDF2-HMAC-SHA256 key stretching (100,000 rounds), match verification, incorrect password rejection, rainbow table mitigation | 4 / 4 | **PASSED** |
| `test_services.py` | Severity score mapping, CSV generation, header and data integrity, automated disk cleanup | 2 / 2 | **PASSED** |
| **Total Automated Tests** | **Comprehensive system verification** | **21 / 21** | **100% PASSED** |

---

## 3. End-to-End Manual Testing Matrix

| Module | Test Action | Expected Result | Pass/Fail |
|---|---|---|---|
| **Auth** | Login with valid credentials (`admin` / `admin123`) | Enters dashboard; audit log recorded in MySQL | Pass |
| **Auth** | Login with incorrect password | Error banner: "Invalid username or password" | Pass |
| **Patients** | Register new patient | Patient created with sequential `PAT-XXXX` code | Pass |
| **Patients** | View medical history modal | Shows patient's past appointments and admissions | Pass |
| **Doctors** | Register new doctor & set department | Added to roster, selectable in booking | Pass |
| **Appointments**| Schedule consultation | Booked on selected date and slot | Pass |
| **Appointments**| Schedule conflicting booking for same doctor/slot | **Blocked**: "Conflict: Doctor already has a scheduled appointment..." | Pass |
| **Appointments**| Schedule conflicting booking for same patient/slot | **Blocked**: "Conflict: Patient already has another appointment..." | Pass |
| **Beds** | Allocate available bed to patient | Status transitions to `Occupied` | Pass |
| **Beds** | Attempt to allocate an occupied bed | **Blocked**: Double-allocation prevention message | Pass |
| **Admissions** | Admit patient to available bed | Admission created; bed locked to Occupied | Pass |
| **Admissions** | Discharge patient with summary & billing | Status set to `Discharged`; **Bed automatically released** to Available | Pass |
| **Emergency** | Register Emergency Case (Critical, High, Med, Low) | Added to queue with corresponding priority score | Pass |
| **Emergency** | Click "Treat Highest Priority Patient" | Pops highest priority patient (Critical before High) | Pass |
| **Analytics** | Open Analytics tab | Renders embedded Matplotlib charts using Pandas DataFrames | Pass |
| **Reports** | Select report type and click "Export to CSV" | CSV saved to `reports_export/`; displays path | Pass |
| **Persistence**| Restart application or Python process | All modifications persist reliably in MySQL | Pass |
