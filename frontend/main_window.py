"""
Main Application Shell.
Provides persistent sidebar navigation, dynamic view switching, active session display,
and responsive window management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Callable
import config
from backend.auth_service import AuthService
from frontend.views.dashboard_view import DashboardView
from frontend.views.patients_view import PatientsView
from frontend.views.doctors_view import DoctorsView
from frontend.views.appointments_view import AppointmentsView
from frontend.views.beds_view import BedsView
from frontend.views.admissions_view import AdmissionsView
from frontend.views.emergency_view import EmergencyView
from frontend.views.analytics_view import AnalyticsView
from frontend.views.reports_view import ReportsView

THEME = config.THEME
FONTS = config.FONTS

class MainWindow(ttk.Frame):
    """Main desktop container with persistent dark sidebar and modular view containers."""

    NAV_ITEMS = [
        ("Dashboard", "Dashboard"),
        ("Patients", "Patients"),
        ("Doctors", "Doctors"),
        ("Appointments", "Appointments"),
        ("Bed Management", "Beds"),
        ("Admissions", "Admissions"),
        ("Emergency Triage", "Emergency"),
        ("Analytics", "Analytics"),
        ("Reports", "Reports"),
    ]

    def __init__(self, parent: tk.Tk, on_logout: Callable, user: Dict[str, Any], **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.parent = parent
        self.on_logout_callback = on_logout
        self.user = user

        self.pack(fill="both", expand=True)

        # Main horizontal split: Sidebar (left) and View Area (right)
        self.sidebar = tk.Frame(self, bg=THEME["bg_sidebar"], width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self, style="TFrame")
        self.content_area.pack(side="right", fill="both", expand=True)

        # Cache of initialized views to allow instant, non-flickering switching
        self.views: Dict[str, ttk.Frame] = {}
        self.active_view_key: Optional[str] = None
        self.nav_buttons: Dict[str, tk.Button] = {}

        # Build Sidebar
        self._build_sidebar()

        # Show Dashboard initially
        self.navigate_to("Dashboard")

    def _build_sidebar(self):
        """Builds brand banner, navigation links, user profile badge, and logout button."""
        # Top Logo & App Title
        brand_frame = tk.Frame(self.sidebar, bg=THEME["bg_sidebar"], padx=16, pady=20)
        brand_frame.pack(fill="x")

        logo_row = tk.Frame(brand_frame, bg=THEME["bg_sidebar"])
        logo_row.pack(fill="x")

        tk.Label(
            logo_row,
            text="+",
            bg=THEME["accent_primary"],
            fg="#ffffff",
            font=("Segoe UI", 14, "bold"),
            width=2,
            height=1
        ).pack(side="left", padx=(0, 10))

        title_box = tk.Frame(logo_row, bg=THEME["bg_sidebar"])
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="MEDICORE",
            bg=THEME["bg_sidebar"],
            fg=THEME["text_primary"],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Hospital Analytics",
            bg=THEME["bg_sidebar"],
            fg=THEME["accent_secondary"],
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        # Divider
        tk.Frame(self.sidebar, bg=THEME["border_color"], height=1).pack(fill="x", padx=14, pady=(10, 14))

        # Nav items container
        nav_container = tk.Frame(self.sidebar, bg=THEME["bg_sidebar"])
        nav_container.pack(fill="both", expand=True)

        for label, key in self.NAV_ITEMS:
            btn = tk.Button(
                nav_container,
                text=f"   {label}",
                bg=THEME["bg_sidebar"],
                fg=THEME["text_secondary"],
                activebackground=THEME["bg_card"],
                activeforeground=THEME["text_primary"],
                font=FONTS["body_bold"],
                anchor="w",
                bd=0,
                padx=16,
                pady=10,
                cursor="hand2",
                command=lambda k=key: self.navigate_to(k)
            )
            btn.pack(fill="x", pady=1)
            self.nav_buttons[key] = btn

        # Divider before profile
        tk.Frame(self.sidebar, bg=THEME["border_color"], height=1).pack(fill="x", padx=14, pady=(10, 10))

        # Bottom Active User Profile Badge
        user_card = tk.Frame(self.sidebar, bg=THEME["bg_card"], padx=12, pady=10)
        user_card.pack(fill="x", padx=12, pady=(0, 8))

        full_name = self.user.get("full_name", "Administrator")
        role = self.user.get("role", "Admin")

        tk.Label(user_card, text=full_name, bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["body_bold"]).pack(anchor="w")
        tk.Label(user_card, text=role, bg=THEME["bg_card"], fg=THEME["accent_secondary"], font=FONTS["caption"]).pack(anchor="w")

        # Logout Button
        logout_btn = tk.Button(
            self.sidebar,
            text="  Sign Out",
            bg="#2a1215",
            fg=THEME["accent_danger"],
            activebackground=THEME["accent_danger"],
            activeforeground="#ffffff",
            font=FONTS["body_bold"],
            anchor="center",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            command=self.confirm_logout
        )
        logout_btn.pack(fill="x", padx=12, pady=(0, 14))

    def navigate_to(self, key: str):
        """Switches the active content panel seamlessly without reloading entire frames unnecessarily."""
        if self.active_view_key == key:
            # If re-clicking the same tab, trigger its refresh
            view = self.views.get(key)
            if hasattr(view, "refresh_all"):
                view.refresh_all()
            elif hasattr(view, "refresh_data"):
                view.refresh_data()
            return

        # Hide current view
        if self.active_view_key and self.active_view_key in self.views:
            self.views[self.active_view_key].pack_forget()

        # Update sidebar button states
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=THEME["sidebar_active"], fg="#ffffff")
            else:
                btn.configure(bg=THEME["bg_sidebar"], fg=THEME["text_secondary"])

        # Instantiate or re-show view
        if key not in self.views:
            self.views[key] = self._create_view(key)

        view = self.views[key]
        view.pack(fill="both", expand=True)
        self.active_view_key = key

        # Trigger data refresh when navigating to the screen
        if hasattr(view, "refresh_all"):
            view.refresh_all()
        elif hasattr(view, "refresh_data"):
            view.refresh_data()
        elif hasattr(view, "load_patients"):
            view.load_patients()
        elif hasattr(view, "load_doctors"):
            view.load_doctors()
        elif hasattr(view, "load_appointments"):
            view.load_appointments()
        elif hasattr(view, "load_admissions"):
            view.load_admissions()
        elif hasattr(view, "render_all_charts"):
            view.render_all_charts()
        elif hasattr(view, "generate_report"):
            view.generate_report()

    def _create_view(self, key: str) -> ttk.Frame:
        """Factory method instantiating the view corresponding to a navigation key."""
        if key == "Dashboard":
            return DashboardView(self.content_area, on_navigate=self.navigate_to)
        elif key == "Patients":
            return PatientsView(self.content_area)
        elif key == "Doctors":
            return DoctorsView(self.content_area)
        elif key == "Appointments":
            return AppointmentsView(self.content_area)
        elif key == "Beds":
            return BedsView(self.content_area)
        elif key == "Admissions":
            return AdmissionsView(self.content_area)
        elif key == "Emergency":
            return EmergencyView(self.content_area)
        elif key == "Analytics":
            return AnalyticsView(self.content_area)
        elif key == "Reports":
            return ReportsView(self.content_area)
        else:
            frame = ttk.Frame(self.content_area, style="TFrame")
            ttk.Label(frame, text=f"Module '{key}'", style="HeaderTitle.TLabel").pack(pady=40)
            return frame

    def confirm_logout(self):
        """Prompts confirmation before terminating user session."""
        confirm = messagebox.askyesno("Sign Out Confirmation", "Are you sure you want to log out of the administrative system?")
        if confirm:
            AuthService.logout()
            self.on_logout_callback()
