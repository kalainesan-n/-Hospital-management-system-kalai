"""
Emergency Management Service.
Implements a Python heapq-based Priority Queue for emergency triage demonstration.

ACADEMIC DISCLAIMER:
This priority queue system is strictly an academic and educational software demonstration
of priority queue data structures (Min-Heap) and is NOT clinically validated or certified
for actual medical triage, diagnosis, or emergency decision making.
"""

import heapq
import itertools
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from database.connection import Database

ACADEMIC_DISCLAIMER = (
    "[ACADEMIC DEMONSTRATION ONLY] This triage priority queue system is an educational simulation "
    "demonstrating Python min-heap algorithmic ordering and is NOT clinically validated for real-world medical care."
)

# Severity score mapping (lower integer indicates higher clinical priority in Min-Heap)
SEVERITY_MAPPING = {
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4
}

class EmergencyPriorityQueue:
    """
    In-memory Min-Heap Priority Queue.
    Stores entries as tuples: (priority_score, sequence_counter, case_dict)
    The sequence counter guarantees strict First-In-First-Out (FIFO) ordering
    for cases with identical triage severity scores.
    """
    def __init__(self):
        self._heap: List[Tuple[int, int, Dict[str, Any]]] = []
        self._counter = itertools.count()
        self._entry_finder: Dict[int, Any] = {}  # maps emergency_id to entry

    def push(self, case: Dict[str, Any]):
        """Inserts a case into the priority queue."""
        priority = case.get("priority_score", 4)
        count = next(self._counter)
        entry = [priority, count, case]
        emergency_id = case.get("emergency_id")
        if emergency_id:
            self._entry_finder[emergency_id] = entry
        heapq.heappush(self._heap, entry)

    def pop(self) -> Optional[Dict[str, Any]]:
        """Pops and returns the highest priority (lowest score) case."""
        while self._heap:
            priority, count, case = heapq.heappop(self._heap)
            if case is not None:
                emergency_id = case.get("emergency_id")
                if emergency_id in self._entry_finder:
                    del self._entry_finder[emergency_id]
                return case
        return None

    def peek(self) -> Optional[Dict[str, Any]]:
        """Returns the highest priority case without removing it."""
        while self._heap:
            priority, count, case = self._heap[0]
            if case is not None:
                return case
            heapq.heappop(self._heap)
        return None

    def get_all_sorted(self) -> List[Dict[str, Any]]:
        """Returns all cases in current priority order without mutating the heap."""
        sorted_entries = sorted([entry for entry in self._heap if entry[2] is not None])
        return [entry[2] for entry in sorted_entries]

    def clear(self):
        """Clears all heap entries."""
        self._heap.clear()
        self._entry_finder.clear()

    def __len__(self):
        return len([e for e in self._heap if e[2] is not None])


class EmergencyService:
    """Coordinates emergency case registration, persistence, and priority queue triage."""

    _queue = EmergencyPriorityQueue()

    @staticmethod
    def generate_case_code() -> str:
        """Generates a sequential emergency case code."""
        with Database() as db:
            row = db.execute_one("SELECT MAX(emergency_id) as max_id FROM emergency_cases")
            next_id = (row['max_id'] or 0) + 1
            return f"EMG-C{next_id:02d}"

    @classmethod
    def sync_queue_from_db(cls):
        """Re-synchronizes the in-memory priority queue from active 'Pending' database cases."""
        cls._queue.clear()
        with Database() as db:
            query = """
                SELECT e.emergency_id, e.case_code, e.patient_name, e.age, e.gender,
                       e.triage_severity, e.priority_score, e.chief_complaint, e.vitals_summary,
                       e.assigned_doctor_id, e.status, e.registered_at, e.notes,
                       CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                FROM emergency_cases e
                LEFT JOIN doctors d ON e.assigned_doctor_id = d.doctor_id
                WHERE e.status = 'Pending'
                ORDER BY e.priority_score ASC, e.registered_at ASC
            """
            cases = db.execute_query(query)
            for c in cases:
                cls._queue.push(c)

    @classmethod
    def get_priority_queue_cases(cls) -> List[Dict[str, Any]]:
        """Returns the current ordered priority list from the queue."""
        cls.sync_queue_from_db()
        return cls._queue.get_all_sorted()

    @classmethod
    def register_case(cls, data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """Registers an emergency patient and enqueues them into the triage priority queue."""
        patient_name = data.get("patient_name", "").strip()
        age = data.get("age")
        gender = data.get("gender", "Other")
        severity = data.get("triage_severity", "Medium")
        chief_complaint = data.get("chief_complaint", "").strip()

        if not patient_name or not chief_complaint or age is None:
            return False, "Patient name, age, and chief complaint are required.", None

        priority_score = SEVERITY_MAPPING.get(severity, 3)
        case_code = data.get("case_code") or cls.generate_case_code()
        reg_time = data.get("registered_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with Database() as db:
                query = """
                    INSERT INTO emergency_cases (
                        case_code, patient_name, age, gender, triage_severity,
                        priority_score, chief_complaint, vitals_summary,
                        assigned_doctor_id, status, registered_at, notes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s)
                """
                params = (
                    case_code,
                    patient_name,
                    int(age),
                    gender,
                    severity,
                    priority_score,
                    chief_complaint,
                    data.get("vitals_summary", "").strip() or None,
                    data.get("assigned_doctor_id") or None,
                    reg_time,
                    data.get("notes", "").strip() or None
                )
                eid = db.execute_insert(query, params)

                # Fetch full case for in-memory queue
                new_case = db.execute_one("SELECT * FROM emergency_cases WHERE emergency_id = %s", (eid,))
                if new_case:
                    cls._queue.push(new_case)

                # Log activity
                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    ("EMERGENCY_REGISTERED", "Emergency", case_code, f"Triage severity: {severity} (Score: {priority_score})")
                )
                return True, f"Emergency case {case_code} registered under severity '{severity}'.", eid
        except Exception as e:
            return False, f"Failed to register emergency case: {str(e)}", None

    @classmethod
    def get_next_patient_to_treat(cls) -> Optional[Dict[str, Any]]:
        """Pops and returns the highest priority emergency patient from the queue."""
        cls.sync_queue_from_db()
        return cls._queue.peek()

    @classmethod
    def process_case(
        cls,
        emergency_id: int,
        new_status: str,
        treatment_notes: Optional[str] = None,
        doctor_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Updates an emergency case status (In Progress, Treated, Admitted, Transferred).
        Refreshes priority queue.
        """
        valid_statuses = ('Pending', 'In Progress', 'Treated', 'Admitted', 'Transferred')
        if new_status not in valid_statuses:
            return False, f"Invalid status '{new_status}'."

        try:
            with Database() as db:
                treated_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status in ('Treated', 'Admitted') else None
                query = """
                    UPDATE emergency_cases
                    SET status = %s, notes = CONCAT(COALESCE(notes, ''), '\n', %s),
                        assigned_doctor_id = COALESCE(%s, assigned_doctor_id),
                        treated_at = COALESCE(%s, treated_at)
                    WHERE emergency_id = %s
                """
                db.execute_non_query(query, (new_status, treatment_notes or f"Status updated to {new_status}", doctor_id, treated_dt, emergency_id))

                db.execute_non_query(
                    "INSERT INTO activity_logs (action, entity_type, entity_id, details) VALUES (%s, %s, %s, %s)",
                    (f"EMERGENCY_{new_status.upper()}", "Emergency", str(emergency_id), f"Case transitioned to {new_status}")
                )

                # Refresh in-memory queue
                cls.sync_queue_from_db()
                return True, f"Emergency case updated to '{new_status}'."
        except Exception as e:
            return False, f"Failed to update emergency case: {str(e)}"

    @classmethod
    def get_all_cases(cls, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all emergency cases from database."""
        with Database() as db:
            if status and status != "All":
                query = """
                    SELECT e.*, CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                    FROM emergency_cases e
                    LEFT JOIN doctors d ON e.assigned_doctor_id = d.doctor_id
                    WHERE e.status = %s
                    ORDER BY e.priority_score ASC, e.registered_at DESC
                """
                return db.execute_query(query, (status,))
            else:
                query = """
                    SELECT e.*, CONCAT('Dr. ', d.first_name, ' ', d.last_name) as doctor_name
                    FROM emergency_cases e
                    LEFT JOIN doctors d ON e.assigned_doctor_id = d.doctor_id
                    ORDER BY e.priority_score ASC, e.registered_at DESC
                """
                return db.execute_query(query)
