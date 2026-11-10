"""
Unit Tests for Emergency Priority Queue Algorithm.
Validates Min-Heap ordering (Critical > High > Medium > Low) and strict FIFO tie-breaking.
"""

import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.emergency_service import EmergencyPriorityQueue, SEVERITY_MAPPING

class TestEmergencyPriorityQueue(unittest.TestCase):
    """Verifies priority queue ordering and FIFO tie-break guarantees."""

    def setUp(self):
        self.pq = EmergencyPriorityQueue()

    def test_priority_ordering(self):
        """Tests that patients with higher clinical urgency (lower score) are popped first."""
        case_low = {"emergency_id": 1, "patient_name": "Low Patient", "priority_score": 4, "triage_severity": "Low"}
        case_med = {"emergency_id": 2, "patient_name": "Med Patient", "priority_score": 3, "triage_severity": "Medium"}
        case_high = {"emergency_id": 3, "patient_name": "High Patient", "priority_score": 2, "triage_severity": "High"}
        case_crit = {"emergency_id": 4, "patient_name": "Critical Patient", "priority_score": 1, "triage_severity": "Critical"}

        # Push in random order: Low, High, Critical, Medium
        self.pq.push(case_low)
        self.pq.push(case_high)
        self.pq.push(case_crit)
        self.pq.push(case_med)

        self.assertEqual(len(self.pq), 4)

        # Expected pop order: Critical (1) -> High (2) -> Medium (3) -> Low (4)
        popped1 = self.pq.pop()
        self.assertEqual(popped1["patient_name"], "Critical Patient")

        popped2 = self.pq.pop()
        self.assertEqual(popped2["patient_name"], "High Patient")

        popped3 = self.pq.pop()
        self.assertEqual(popped3["patient_name"], "Med Patient")

        popped4 = self.pq.pop()
        self.assertEqual(popped4["patient_name"], "Low Patient")

        self.assertEqual(len(self.pq), 0)
        self.assertIsNone(self.pq.pop())

    def test_fifo_tie_breaking(self):
        """Tests that cases with the exact same severity score preserve strict arrival order (FIFO)."""
        crit_first = {"emergency_id": 10, "patient_name": "First Critical", "priority_score": 1}
        crit_second = {"emergency_id": 11, "patient_name": "Second Critical", "priority_score": 1}
        crit_third = {"emergency_id": 12, "patient_name": "Third Critical", "priority_score": 1}

        self.pq.push(crit_first)
        self.pq.push(crit_second)
        self.pq.push(crit_third)

        # Must pop in exact arrival sequence
        self.assertEqual(self.pq.pop()["patient_name"], "First Critical")
        self.assertEqual(self.pq.pop()["patient_name"], "Second Critical")
        self.assertEqual(self.pq.pop()["patient_name"], "Third Critical")

    def test_peek_does_not_remove(self):
        """Tests that peek() inspects the top item without mutating the heap size."""
        case = {"emergency_id": 99, "patient_name": "Test", "priority_score": 2}
        self.pq.push(case)
        self.assertEqual(len(self.pq), 1)

        peeked = self.pq.peek()
        self.assertEqual(peeked["patient_name"], "Test")
        self.assertEqual(len(self.pq), 1)

    def test_get_all_sorted(self):
        """Tests non-destructive extraction of all queued cases in priority order."""
        c1 = {"emergency_id": 1, "patient_name": "C1", "priority_score": 3}
        c2 = {"emergency_id": 2, "patient_name": "C2", "priority_score": 1}
        c3 = {"emergency_id": 3, "patient_name": "C3", "priority_score": 2}

        self.pq.push(c1)
        self.pq.push(c2)
        self.pq.push(c3)

        sorted_list = self.pq.get_all_sorted()
        names = [item["patient_name"] for item in sorted_list]
        self.assertEqual(names, ["C2", "C3", "C1"])
        # Original heap length preserved
        self.assertEqual(len(self.pq), 3)

if __name__ == "__main__":
    unittest.main()
