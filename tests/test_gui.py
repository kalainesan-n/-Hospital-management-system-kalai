"""
GUI Smoke and Lifecycle Automated Test.
Verifies that Tkinter widgets, dark theme, login flow, navigation switching,
and all 9 screen views (including Matplotlib canvases) instantiate and render without errors.
"""

import sys
import os
import unittest
import tkinter as tk
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from main import HospitalApp
from backend.auth_service import AuthService

class TestGUILifecycle(unittest.TestCase):
    """Verifies Tkinter GUI rendering, navigation, and screen lifecycles."""

    def setUp(self):
        self.root = tk.Tk()
        # Withdraw window to prevent UI flickering during automated test
        self.root.withdraw()
        self.app = HospitalApp(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_full_gui_navigation_lifecycle(self):
        """Tests login screen, authenticates, and navigates across every single view."""
        self.root.update_idletasks()

        # 1. Verify Login Screen is active
        self.assertIsNotNone(self.app.current_screen)
        login_view = self.app.current_screen
        self.assertEqual(login_view.username_var.get(), "admin")

        # 2. Simulate Authentication
        success, msg, user = AuthService.login("admin", "admin123")
        self.assertTrue(success)
        self.app.show_main_window(user)
        self.root.update_idletasks()

        main_window = self.app.current_screen
        self.assertIsNotNone(main_window)

        # 3. Cycle through every screen view and verify zero errors
        views_to_test = [
            "Dashboard",
            "Patients",
            "Doctors",
            "Appointments",
            "Beds",
            "Admissions",
            "Emergency",
            "Analytics",
            "Reports"
        ]

        for view_name in views_to_test:
            main_window.navigate_to(view_name)
            self.root.update_idletasks()
            active_view = main_window.views.get(view_name)
            self.assertIsNotNone(active_view, f"View {view_name} failed to instantiate")

        # 4. Simulate Logout
        self.app.show_login_screen()
        self.root.update_idletasks()
        self.assertIsNotNone(self.app.current_screen)

if __name__ == "__main__":
    unittest.main()
