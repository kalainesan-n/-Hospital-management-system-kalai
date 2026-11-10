"""
Appointment Management View.
Implements scheduling with double-booking prevention, status changes, and date/status filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
from datetime import date, datetime
import config
from frontend.components import HeaderBar, SearchBar, StyledTreeview, ModalDialog
from backend.appointment_service import AppointmentService
from backend.patient_service import PatientService
from backend.doctor_service import DoctorService

THEME = config.THEME
FONTS = config.FONTS

class AppointmentsView(ttk.Frame):
    """Clinical appointment scheduling and management screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Appointment Management",
            subtitle="Schedule outpatient consultations with anti-double-booking safeguards for doctors and patients",
            on_refresh=self.load_appointments
        )
        self.header.pack(fill="x")

        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        self.search_bar = SearchBar(toolbar, placeholder="Search by patient, doctor, code, or clinical reason...", on_search=self.filter_appointments)
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Status Filter
        tk.Label(toolbar, text="Status:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.status_var = tk.StringVar(value="All")
        self.status_cb = ttk.Combobox(toolbar, textvariable=self.status_var, values=["All", "Scheduled", "Completed", "Cancelled", "No-Show"], state="readonly", width=12)
        self.status_cb.pack(side="left", padx=(0, 10))
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_appointments(self.search_bar.get()))

        # Quick Today filter
        today_btn = ttk.Button(toolbar, text="Today", style="Secondary.TButton", command=self.set_filter_today)
        today_btn.pack(side="left", padx=(0, 6))

        all_dates_btn = ttk.Button(toolbar, text="All Dates", style="Secondary.TButton", command=self.clear_date_filter)
        all_dates_btn.pack(side="left", padx=(0, 10))

        book_btn = ttk.Button(toolbar, text="+ Book Appointment", style="Success.TButton", command=self.open_schedule_dialog)
        book_btn.pack(side="right")

        self.active_date_filter: Optional[str] = None

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "code", "date", "time", "patient", "doctor", "dept", "reason", "status"],
            headings=["ID", "Code", "Date", "Time", "Patient Name", "Consulting Doctor", "Department", "Clinical Reason", "Status"],
            widths=[45, 80, 85, 65, 140, 140, 120, 160, 85]
        )
        self.table.pack(fill="both", expand=True)

        # Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        complete_btn = ttk.Button(action_bar, text="Mark as Completed", style="Success.TButton", command=self.handle_mark_completed)
        complete_btn.pack(side="left", padx=(0, 8))

        cancel_btn = ttk.Button(action_bar, text="Cancel Appointment", style="Danger.TButton", command=self.handle_cancel)
        cancel_btn.pack(side="left", padx=(0, 8))

        edit_btn = ttk.Button(action_bar, text="Reschedule / Edit", style="Secondary.TButton", command=self.open_edit_dialog)
        edit_btn.pack(side="left")

        self.count_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.count_lbl.pack(side="right")

        self.load_appointments()

    def set_filter_today(self):
        self.active_date_filter = date.today().strftime("%Y-%m-%d")
        self.load_appointments(self.search_bar.get())

    def clear_date_filter(self):
        self.active_date_filter = None
        self.load_appointments(self.search_bar.get())

    def load_appointments(self, search_term: Optional[str] = None):
        """Fetches and displays appointments."""
        try:
            status = self.status_var.get()
            apps = AppointmentService.get_all_appointments(search_term, status, self.active_date_filter)
            rows = [
                [
                    a["appointment_id"],
                    a["appointment_code"],
                    str(a["appointment_date"]),
                    str(a["appointment_time"])[:5],
                    a["patient_name"],
                    a["doctor_name"],
                    a["department"],
                    a["reason"] or "-",
                    a["status"]
                ]
                for a in apps
            ]
            self.table.insert_rows(rows)
            filter_note = f" (Date: {self.active_date_filter})" if self.active_date_filter else ""
            self.count_lbl.configure(text=f"Total: {len(rows)}{filter_note}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load appointments: {e}")

    def filter_appointments(self, term: str):
        self.load_appointments(term if term else None)

    def get_selected_appointment_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an appointment from the list.")
            return None
        return int(selected[0])

    def open_schedule_dialog(self):
        """Opens booking modal with patient/doctor selectors and live anti-conflict validation."""
        patients = PatientService.get_all_patients()
        doctors = DoctorService.get_all_doctors(status="Active")

        if not patients:
            messagebox.showwarning("Notice", "Please register at least one patient before scheduling appointments.")
            return
        if not doctors:
            messagebox.showwarning("Notice", "No active doctors available for consultation.")
            return

        dialog = ModalDialog(self, title="Schedule New Consultation", width=560, height=580)

        # Patient Dropdown
        row_pat = ttk.Frame(dialog.body_frame, style="TFrame")
        row_pat.pack(fill="x", pady=6)
        tk.Label(row_pat, text="Patient *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        patient_map = {f"[{p['patient_code']}] {p['full_name']} (Phone: {p['phone']})": p['patient_id'] for p in patients}
        patient_options = list(patient_map.keys())
        patient_var = tk.StringVar(value=patient_options[0])
        pat_cb = ttk.Combobox(row_pat, textvariable=patient_var, values=patient_options, state="readonly")
        pat_cb.pack(side="left", fill="x", expand=True)

        # Doctor Dropdown
        row_doc = ttk.Frame(dialog.body_frame, style="TFrame")
        row_doc.pack(fill="x", pady=6)
        tk.Label(row_doc, text="Consulting Doctor *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        doctor_map = {f"[{d['doctor_code']}] {d['full_name']} — {d['specialization']} ({d['shift_time']})": d['doctor_id'] for d in doctors}
        doctor_options = list(doctor_map.keys())
        doctor_var = tk.StringVar(value=doctor_options[0])
        doc_cb = ttk.Combobox(row_doc, textvariable=doctor_var, values=doctor_options, state="readonly")
        doc_cb.pack(side="left", fill="x", expand=True)

        # Date Entry
        row_dt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_dt.pack(fill="x", pady=6)
        tk.Label(row_dt, text="Date (YYYY-MM-DD) *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        ttk.Entry(row_dt, textvariable=date_var).pack(side="left", fill="x", expand=True)

        # Time Slot Selector
        row_tm = ttk.Frame(dialog.body_frame, style="TFrame")
        row_tm.pack(fill="x", pady=6)
        tk.Label(row_tm, text="Time Slot *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        time_slots = [
            "09:00:00", "09:30:00", "10:00:00", "10:30:00", "11:00:00", "11:30:00",
            "12:00:00", "12:30:00", "14:00:00", "14:30:00", "15:00:00", "15:30:00",
            "16:00:00", "16:30:00", "17:00:00"
        ]
        time_var = tk.StringVar(value="09:30:00")
        time_cb = ttk.Combobox(row_tm, textvariable=time_var, values=time_slots)
        time_cb.pack(side="left", fill="x", expand=True)

        # Clinical Reason
        row_rs = ttk.Frame(dialog.body_frame, style="TFrame")
        row_rs.pack(fill="x", pady=6)
        tk.Label(row_rs, text="Chief Reason *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        reason_var = tk.StringVar()
        ttk.Entry(row_rs, textvariable=reason_var).pack(side="left", fill="x", expand=True)

        # Notes
        row_nt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_nt.pack(fill="x", pady=6)
        tk.Label(row_nt, text="Special Notes", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        notes_var = tk.StringVar()
        ttk.Entry(row_nt, textvariable=notes_var).pack(side="left", fill="x", expand=True)

        # Anti-conflict info banner
        info_banner = tk.Label(
            dialog.body_frame,
            text="Automatic Conflict Prevention: The system will verify that neither the selected doctor nor patient has overlapping appointments.",
            bg=THEME["bg_card"],
            fg=THEME["accent_secondary"],
            font=FONTS["caption"],
            wraplength=480,
            padx=10,
            pady=8
        )
        info_banner.pack(fill="x", pady=(12, 0))

        def book():
            pid = patient_map.get(patient_var.get())
            did = doctor_map.get(doctor_var.get())
            dt = date_var.get().strip()
            tm = time_var.get().strip()
            reason = reason_var.get().strip()

            if not reason:
                dialog.show_error("Please specify the chief reason for consultation.")
                return

            # Ensure time has HH:MM:SS format
            if len(tm) == 5:
                tm += ":00"

            data = {
                "patient_id": pid,
                "doctor_id": did,
                "appointment_date": dt,
                "appointment_time": tm,
                "reason": reason,
                "notes": notes_var.get().strip()
            }

            success, msg, _ = AppointmentService.schedule_appointment(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_appointments()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Confirm Appointment", style="Success.TButton", command=book).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def handle_mark_completed(self):
        """Sets appointment status to Completed."""
        app_id = self.get_selected_appointment_id()
        if not app_id:
            return

        success, msg = AppointmentService.update_status(app_id, "Completed", "Consultation conducted and completed.")
        if success:
            messagebox.showinfo("Status Updated", msg)
            self.load_appointments()
        else:
            messagebox.showerror("Error", msg)

    def handle_cancel(self):
        """Cancels selected appointment."""
        app_id = self.get_selected_appointment_id()
        if not app_id:
            return

        confirm = messagebox.askyesno("Cancel Appointment", "Are you sure you want to cancel this appointment?")
        if not confirm:
            return

        success, msg = AppointmentService.update_status(app_id, "Cancelled", "Cancelled by clinic administration.")
        if success:
            messagebox.showinfo("Cancelled", msg)
            self.load_appointments()
        else:
            messagebox.showerror("Error", msg)

    def open_edit_dialog(self):
        """Reschedules or updates appointment date/time/reason with conflict checks."""
        app_id = self.get_selected_appointment_id()
        if not app_id:
            return

        # Fetch appointment details
        apps = AppointmentService.get_all_appointments()
        target = next((a for a in apps if a["appointment_id"] == app_id), None)
        if not target:
            messagebox.showerror("Error", "Appointment record not found.")
            return

        dialog = ModalDialog(self, title=f"Reschedule Appointment — {target['appointment_code']}", width=520, height=480)

        tk.Label(dialog.body_frame, text=f"Patient: {target['patient_name']} | Doctor: {target['doctor_name']}", bg=THEME["bg_dark"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w", pady=(0, 10))

        # Date Entry
        row_dt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_dt.pack(fill="x", pady=6)
        tk.Label(row_dt, text="New Date (YYYY-MM-DD)", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=20, anchor="w").pack(side="left")
        date_var = tk.StringVar(value=str(target["appointment_date"]))
        ttk.Entry(row_dt, textvariable=date_var).pack(side="left", fill="x", expand=True)

        # Time Entry
        row_tm = ttk.Frame(dialog.body_frame, style="TFrame")
        row_tm.pack(fill="x", pady=6)
        tk.Label(row_tm, text="New Time (HH:MM:SS)", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=20, anchor="w").pack(side="left")
        time_var = tk.StringVar(value=str(target["appointment_time"]))
        ttk.Entry(row_tm, textvariable=time_var).pack(side="left", fill="x", expand=True)

        # Reason
        row_rs = ttk.Frame(dialog.body_frame, style="TFrame")
        row_rs.pack(fill="x", pady=6)
        tk.Label(row_rs, text="Reason / Update", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=20, anchor="w").pack(side="left")
        reason_var = tk.StringVar(value=target["reason"] or "")
        ttk.Entry(row_rs, textvariable=reason_var).pack(side="left", fill="x", expand=True)

        # Status
        row_st = ttk.Frame(dialog.body_frame, style="TFrame")
        row_st.pack(fill="x", pady=6)
        tk.Label(row_st, text="Status", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=20, anchor="w").pack(side="left")
        status_var = tk.StringVar(value=target["status"])
        ttk.Combobox(row_st, textvariable=status_var, values=["Scheduled", "Completed", "Cancelled", "No-Show"], state="readonly").pack(side="left", fill="x", expand=True)

        def save():
            dt = date_var.get().strip()
            tm = time_var.get().strip()
            if len(tm) == 5:
                tm += ":00"

            data = {
                "patient_id": target["patient_id"],
                "doctor_id": target["doctor_id"],
                "appointment_date": dt,
                "appointment_time": tm,
                "reason": reason_var.get().strip(),
                "status": status_var.get(),
                "notes": f"Updated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }

            success, msg = AppointmentService.update_appointment(app_id, data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_appointments()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Save Changes", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
