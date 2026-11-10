"""
Unit Tests for Service Layer Helpers and Reporting.
Validates code generation formats, CSV export functions, and validation boundaries.
"""

import sys
import os
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.report_service import ReportService
from backend.emergency_service import SEVERITY_MAPPING

class TestServiceHelpers(unittest.TestCase):
    """Verifies reporting formats and business logic mappings."""

    def test_severity_mapping(self):
        """Verifies that clinical triage severity ranks match the Min-Heap priority scale."""
        self.assertEqual(SEVERITY_MAPPING["Critical"], 1)
        self.assertEqual(SEVERITY_MAPPING["High"], 2)
        self.assertEqual(SEVERITY_MAPPING["Medium"], 3)
        self.assertEqual(SEVERITY_MAPPING["Low"], 4)

    def test_csv_export(self):
        """Tests that CSV export writes headers and rows to a readable file."""
        headers = ["ID", "Name", "Role", "Score"]
        data = [
            [1, "Alice Test", "Doctor", 95.5],
            [2, "Bob Test", "Patient", 80.0]
        ]
        success, filepath = ReportService.export_to_csv(headers, data, filename_prefix="unit_test_export")
        self.assertTrue(success)
        self.assertTrue(os.path.isfile(filepath))

        # Read back and verify content
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 3)
            self.assertIn("Alice Test", lines[1])
            self.assertIn("Bob Test", lines[2])

        # Cleanup test file
        try:
            os.remove(filepath)
        except OSError:
            pass

if __name__ == "__main__":
    unittest.main()
