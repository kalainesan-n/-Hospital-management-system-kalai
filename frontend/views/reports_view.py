"""
Reports View.
Provides tabular audit reports across all modules with date filtering and CSV export capabilities.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, List
from datetime import date
import config
from frontend.components import HeaderBar, StyledTreeview
from backend.report_service import ReportService

THEME = config.THEME
FONTS = config.FONTS

class ReportsView(ttk.Frame):
    """Clinical audit and administrative report generation screen with CSV export."""

    REPORT_TYPES = [
        "Patients Master Registry",
        "Doctors Directory",
        "Appointments Report",
        "Bed Occupancy & Inventory",
        "Inpatient Admissions & Discharges",
        "Emergency Triage Logs"
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Operational Reports & Data Export",
            subtitle="Filter, inspect, and export audit-ready tabular reports to CSV format",
            on_refresh=self.generate_report
        )
        self.header.pack(fill="x")

        # Filter Controls Frame
        filter_card = tk.Frame(self, bg=THEME["bg_card"], padx=16, pady=12)
        filter_card.pack(fill="x", pady=(0, 14))

        # Row 1: Report Type + Dates + Generate
        r1 = ttk.Frame(filter_card, style="Card.TFrame")
        r1.pack(fill="x")

        tk.Label(r1, text="Report Type:", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 6))
        self.type_var = tk.StringVar(value=self.REPORT_TYPES[0])
        self.type_cb = ttk.Combobox(r1, textvariable=self.type_var, values=self.REPORT_TYPES, state="readonly", width=32)
        self.type_cb.pack(side="left", padx=(0, 16))
        self.type_cb.bind("<<ComboboxSelected>>", lambda e: self.generate_report())

        tk.Label(r1, text="From Date:", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 6))
        self.from_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self.from_var, width=12).pack(side="left", padx=(0, 12))

        tk.Label(r1, text="To Date:", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 6))
        self.to_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self.to_var, width=12).pack(side="left", padx=(0, 16))

        gen_btn = ttk.Button(r1, text="Generate Report", style="TButton", command=self.generate_report)
        gen_btn.pack(side="left", padx=(0, 10))

        export_btn = ttk.Button(r1, text="Export to CSV", style="Success.TButton", command=self.export_csv)
        export_btn.pack(side="right")

        # Container for Dynamic Table
        self.table_container = ttk.Frame(self, style="TFrame")
        self.table_container.pack(fill="both", expand=True)

        self.current_headers: List[str] = []
        self.current_data: List[List[Any]] = []
        self.tree_widget: Optional[StyledTreeview] = None

        # Bottom status bar
        self.status_bar = ttk.Frame(self, style="TFrame", padding=(0, 8, 0, 0))
        self.status_bar.pack(fill="x")

        self.status_lbl = tk.Label(self.status_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.status_lbl.pack(side="left")

        self.generate_report()

    def generate_report(self):
        """Generates report rows according to selected filters."""
        rpt = self.type_var.get()
        start_dt = self.from_var.get().strip() or None
        end_dt = self.to_var.get().strip() or None

        try:
            if rpt == "Patients Master Registry":
                headers, data = ReportService.get_patient_report(start_dt, end_dt)
            elif rpt == "Doctors Directory":
                headers, data = ReportService.get_doctor_report()
            elif rpt == "Appointments Report":
                headers, data = ReportService.get_appointment_report(start_dt, end_dt)
            elif rpt == "Bed Occupancy & Inventory":
                headers, data = ReportService.get_bed_occupancy_report()
            elif rpt == "Inpatient Admissions & Discharges":
                headers, data = ReportService.get_admission_report(start_dt, end_dt)
            elif rpt == "Emergency Triage Logs":
                headers, data = ReportService.get_emergency_report(start_dt, end_dt)
            else:
                headers, data = [], []

            self.current_headers = headers
            self.current_data = data

            # Rebuild Treeview dynamically
            if self.tree_widget:
                self.tree_widget.destroy()

            cols = [f"c_{i}" for i in range(len(headers))]
            widths = [max(80, min(220, len(h) * 14)) for h in headers]
            self.tree_widget = StyledTreeview(self.table_container, columns=cols, headings=headers, widths=widths)
            self.tree_widget.pack(fill="both", expand=True)
            self.tree_widget.insert_rows(data)

            self.status_lbl.configure(text=f"Report Generated: {len(data)} rows loaded for '{rpt}'")
        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report: {e}")

    def export_csv(self):
        """Exports the current report rows to a CSV file."""
        if not self.current_data:
            messagebox.showwarning("Notice", "No data rows available to export.")
            return

        prefix = self.type_var.get().lower().replace(" ", "_").replace("&", "and")
        success, result_path = ReportService.export_to_csv(self.current_headers, self.current_data, filename_prefix=prefix)

        if success:
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(self.current_data)} rows to CSV file:\n\n{result_path}"
            )
        else:
            messagebox.showerror("Export Failed", result_path)
