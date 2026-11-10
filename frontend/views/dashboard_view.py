"""
Dashboard View.
Displays live MySQL-derived operational KPIs, today's schedule, and real-time audit trail.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import config
from frontend.components import StatCard, HeaderBar, StyledTreeview
from backend.dashboard_service import DashboardService

THEME = config.THEME
FONTS = config.FONTS

class DashboardView(ttk.Frame):
    """Real-time executive hospital operations dashboard."""

    def __init__(self, parent, on_navigate: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)
        self.on_navigate = on_navigate

        # Header
        self.header = HeaderBar(
            self,
            title="Operational Dashboard",
            subtitle="Real-time MySQL operational statistics, bed status, and emergency alerts",
            on_refresh=self.refresh_data
        )
        self.header.pack(fill="x")

        # Scrollable container for dashboard
        canvas = tk.Canvas(self, bg=THEME["bg_dark"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        self.content_frame = ttk.Frame(canvas, style="TFrame")

        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas_win = canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(canvas_win, width=e.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Row 1: KPI Stat Cards Grid (6 cards across 2 sub-rows)
        cards_frame = ttk.Frame(self.content_frame, style="TFrame")
        cards_frame.pack(fill="x", pady=(0, 20))

        # 3 columns layout
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)

        self.card_patients = StatCard(cards_frame, title="Total Patients", value="--", subtitle="Registered in hospital", accent_color=THEME["accent_primary"])
        self.card_patients.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        self.card_doctors = StatCard(cards_frame, title="Medical Staff", value="--", subtitle="Active consulting doctors", accent_color=THEME["accent_secondary"])
        self.card_doctors.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)

        self.card_appointments = StatCard(cards_frame, title="Today's Appointments", value="--", subtitle="Scheduled consultations", accent_color=THEME["accent_warning"])
        self.card_appointments.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)

        self.card_occupancy = StatCard(cards_frame, title="Bed Occupancy", value="--%", subtitle="Available: -- | Occupied: --", accent_color=THEME["accent_success"])
        self.card_occupancy.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        self.card_admissions = StatCard(cards_frame, title="Active Admissions", value="--", subtitle="In-patient hospitalizations", accent_color="#8b5cf6")
        self.card_admissions.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

        self.card_emergency = StatCard(cards_frame, title="Emergency Queue", value="--", subtitle="Critical cases pending", accent_color=THEME["accent_danger"])
        self.card_emergency.grid(row=1, column=2, sticky="nsew", padx=6, pady=6)

        # Row 2: Today's Appointments & Recent Activity
        bottom_grid = ttk.Frame(self.content_frame, style="TFrame")
        bottom_grid.pack(fill="both", expand=True)
        bottom_grid.columnconfigure(0, weight=3)
        bottom_grid.columnconfigure(1, weight=2)

        # Left: Today's Appointments
        left_card = tk.Frame(bottom_grid, bg=THEME["bg_card"], padx=14, pady=14)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(left_card, text="TODAY'S SCHEDULED APPOINTMENTS", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w", pady=(0, 10))

        self.app_table = StyledTreeview(
            left_card,
            columns=["code", "time", "patient", "doctor", "department", "status"],
            headings=["Code", "Time", "Patient", "Doctor", "Department", "Status"],
            widths=[80, 70, 140, 130, 120, 80]
        )
        self.app_table.pack(fill="both", expand=True)

        # Right: System Activity & Audit Trail
        right_card = tk.Frame(bottom_grid, bg=THEME["bg_card"], padx=14, pady=14)
        right_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(right_card, text="LIVE RECENT ACTIVITY", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w", pady=(0, 10))

        self.activity_table = StyledTreeview(
            right_card,
            columns=["action", "entity", "details", "time"],
            headings=["Action", "Target", "Details", "Timestamp"],
            widths=[110, 80, 180, 110]
        )
        self.activity_table.pack(fill="both", expand=True)

        self.refresh_data()

    def refresh_data(self):
        """Pulls latest stats directly from MySQL."""
        try:
            metrics = DashboardService.get_live_metrics()

            self.card_patients.update_value(metrics["total_patients"], f"Database total")
            self.card_doctors.update_value(f"{metrics['active_doctors']} / {metrics['total_doctors']}", f"{metrics['active_doctors']} currently active")
            self.card_appointments.update_value(metrics["today_appointments"], f"Total recorded: {metrics['total_appointments']}")
            self.card_occupancy.update_value(
                f"{metrics['bed_occupancy_pct']}%",
                f"Avail: {metrics['available_beds']} | Occ: {metrics['occupied_beds']}"
            )
            self.card_admissions.update_value(metrics["active_admissions"], "Currently admitted")
            self.card_emergency.update_value(
                f"{metrics['pending_emergencies']}",
                f"{metrics['critical_emergencies']} Critical in queue"
            )

            # Update Today's Appointments table
            apps = DashboardService.get_today_appointments_preview(8)
            app_rows = [
                [a["appointment_code"], str(a["appointment_time"])[:5], a["patient_name"], a["doctor_name"], a["department"], a["status"]]
                for a in apps
            ]
            self.app_table.insert_rows(app_rows)

            # Update Recent Activity
            logs = DashboardService.get_recent_activity(8)
            log_rows = [
                [l["action"], f"{l['entity_type']} {l['entity_id'] or ''}", l["details"], str(l["created_at"])[:19]]
                for l in logs
            ]
            self.activity_table.insert_rows(log_rows)

        except Exception as e:
            pass
