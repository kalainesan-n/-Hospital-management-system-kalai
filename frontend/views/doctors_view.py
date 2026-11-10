"""
Doctor Management View.
Implements doctor profile CRUD, availability shifts, department filters, and appointment history.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
import config
from frontend.components import HeaderBar, SearchBar, StyledTreeview, ModalDialog
from backend.doctor_service import DoctorService

THEME = config.THEME
FONTS = config.FONTS

class DoctorsView(ttk.Frame):
    """Physician and medical specialist management screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Doctor Management",
            subtitle="Manage medical specialists, department allocations, consulting fees, and clinical schedules",
            on_refresh=self.load_doctors
        )
        self.header.pack(fill="x")

        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        self.search_bar = SearchBar(toolbar, placeholder="Search doctor by name, code, or specialization...", on_search=self.filter_doctors)
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Department Filter
        tk.Label(toolbar, text="Dept:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.dept_var = tk.StringVar(value="All")
        self.dept_cb = ttk.Combobox(toolbar, textvariable=self.dept_var, state="readonly", width=18)
        self.dept_cb.pack(side="left", padx=(0, 10))
        self.dept_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_doctors(self.search_bar.get()))

        # Status Filter
        tk.Label(toolbar, text="Status:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.status_var = tk.StringVar(value="All")
        self.status_cb = ttk.Combobox(toolbar, textvariable=self.status_var, values=["All", "Active", "On Leave", "Inactive"], state="readonly", width=10)
        self.status_cb.pack(side="left", padx=(0, 10))
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_doctors(self.search_bar.get()))

        add_btn = ttk.Button(toolbar, text="+ Add Doctor", style="Success.TButton", command=self.open_add_dialog)
        add_btn.pack(side="right")

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "code", "name", "specialization", "department", "phone", "email", "fee", "shift", "status"],
            headings=["ID", "Code", "Doctor Name", "Specialization", "Department", "Phone", "Email", "Fee ($)", "Shift Time", "Status"],
            widths=[45, 75, 140, 130, 130, 95, 140, 70, 120, 75]
        )
        self.table.pack(fill="both", expand=True)

        # Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        view_app_btn = ttk.Button(action_bar, text="View Appointments Schedule", style="TButton", command=self.open_schedule_dialog)
        view_app_btn.pack(side="left", padx=(0, 8))

        edit_btn = ttk.Button(action_bar, text="Edit Doctor Profile", style="Secondary.TButton", command=self.open_edit_dialog)
        edit_btn.pack(side="left", padx=(0, 8))

        del_btn = ttk.Button(action_bar, text="Remove Doctor", style="Danger.TButton", command=self.handle_delete)
        del_btn.pack(side="left")

        self.count_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.count_lbl.pack(side="right")

        self.load_departments()
        self.load_doctors()

    def load_departments(self):
        try:
            depts = DoctorService.get_departments()
            self.dept_cb.configure(values=["All"] + depts)
        except Exception:
            pass

    def load_doctors(self, search_term: Optional[str] = None):
        """Fetches doctors and refreshes table."""
        try:
            dept = self.dept_var.get()
            status = self.status_var.get()
            doctors = DoctorService.get_all_doctors(search_term, dept, status)
            rows = [
                [
                    d["doctor_id"],
                    d["doctor_code"],
                    d["full_name"],
                    d["specialization"],
                    d["department"],
                    d["phone"],
                    d["email"],
                    f"${float(d['consultation_fee']):.2f}",
                    d["shift_time"],
                    d["status"]
                ]
                for d in doctors
            ]
            self.table.insert_rows(rows)
            self.count_lbl.configure(text=f"Total Doctors: {len(rows)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load doctors: {e}")

    def filter_doctors(self, term: str):
        self.load_doctors(term if term else None)

    def get_selected_doctor_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a doctor from the list.")
            return None
        return int(selected[0])

    def open_add_dialog(self):
        """Opens popup dialog to register a doctor."""
        dialog = ModalDialog(self, title="Register New Consulting Doctor", width=540, height=640)
        entries = self._build_doctor_form(dialog.body_frame)

        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["first_name"] or not data["last_name"] or not data["specialization"] or not data["department"] or not data["phone"]:
                dialog.show_error("First Name, Last Name, Specialization, Department, and Phone are required.")
                return

            try:
                data["consultation_fee"] = float(data["consultation_fee"]) if data["consultation_fee"] else 500.0
            except ValueError:
                dialog.show_error("Consultation fee must be a valid number.")
                return

            success, msg, _ = DoctorService.create_doctor(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_departments()
                self.load_doctors()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Register Doctor", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def open_edit_dialog(self):
        """Opens popup to edit doctor profile."""
        doctor_id = self.get_selected_doctor_id()
        if not doctor_id:
            return

        doc = DoctorService.get_doctor_by_id(doctor_id)
        if not doc:
            messagebox.showerror("Error", "Doctor details not found.")
            return

        dialog = ModalDialog(self, title=f"Edit Profile — {doc['full_name']} ({doc['doctor_code']})", width=540, height=640)
        entries = self._build_doctor_form(dialog.body_frame, doc)

        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["first_name"] or not data["last_name"] or not data["specialization"] or not data["department"] or not data["phone"]:
                dialog.show_error("First Name, Last Name, Specialization, Department, and Phone are required.")
                return

            try:
                data["consultation_fee"] = float(data["consultation_fee"]) if data["consultation_fee"] else 500.0
            except ValueError:
                dialog.show_error("Consultation fee must be a valid number.")
                return

            success, msg = DoctorService.update_doctor(doctor_id, data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_departments()
                self.load_doctors()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Save Changes", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def _build_doctor_form(self, container: ttk.Frame, initial: Optional[Dict[str, Any]] = None) -> Dict[str, tk.StringVar]:
        entries = {}
        fields = [
            ("first_name", "First Name *", initial.get("first_name", "") if initial else ""),
            ("last_name", "Last Name *", initial.get("last_name", "") if initial else ""),
            ("specialization", "Specialization *", initial.get("specialization", "") if initial else ""),
            ("department", "Department *", initial.get("department", "") if initial else ""),
            ("phone", "Phone Number *", initial.get("phone", "") if initial else ""),
            ("email", "Email Address", initial.get("email", "") if initial else ""),
            ("qualification", "Medical Qualifications", initial.get("qualification", "") if initial else ""),
            ("consultation_fee", "Consultation Fee ($)", str(initial.get("consultation_fee", "500.0")) if initial else "500.0"),
            ("available_days", "Available Days", initial.get("available_days", "Mon,Tue,Wed,Thu,Fri") if initial else "Mon,Tue,Wed,Thu,Fri"),
            ("shift_time", "Shift Timing", initial.get("shift_time", "09:00 AM - 05:00 PM") if initial else "09:00 AM - 05:00 PM"),
        ]

        for key, label, val in fields:
            row = ttk.Frame(container, style="TFrame")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=val)
            ent = ttk.Entry(row, textvariable=var)
            ent.pack(side="left", fill="x", expand=True)
            entries[key] = var

        # Status row
        status_row = ttk.Frame(container, style="TFrame")
        status_row.pack(fill="x", pady=4)
        tk.Label(status_row, text="Practice Status", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=22, anchor="w").pack(side="left")
        status_var = tk.StringVar(value=initial.get("status", "Active") if initial else "Active")
        cb = ttk.Combobox(status_row, textvariable=status_var, values=["Active", "On Leave", "Inactive"], state="readonly")
        cb.pack(side="left", fill="x", expand=True)
        entries["status"] = status_var

        return entries

    def handle_delete(self):
        """Removes doctor profile after confirmation."""
        doctor_id = self.get_selected_doctor_id()
        if not doctor_id:
            return

        confirm = messagebox.askyesno("Confirm Removal", "Are you sure you want to remove this doctor from the roster?")
        if not confirm:
            return

        success, msg = DoctorService.delete_doctor(doctor_id)
        if success:
            messagebox.showinfo("Removed", msg)
            self.load_doctors()
        else:
            messagebox.showerror("Error", msg)

    def open_schedule_dialog(self):
        """Opens schedule and appointment bookings dialog for selected doctor."""
        doctor_id = self.get_selected_doctor_id()
        if not doctor_id:
            return

        doc = DoctorService.get_doctor_by_id(doctor_id)
        apps = DoctorService.get_doctor_appointments(doctor_id)

        dialog = ModalDialog(self, title=f"Consultation Schedule — {doc['full_name']} ({doc['specialization']})", width=700, height=520)

        info_box = tk.Frame(dialog.body_frame, bg=THEME["bg_card"], padx=14, pady=10)
        info_box.pack(fill="x", pady=(0, 10))
        tk.Label(info_box, text=f"{doc['full_name']} | Dept: {doc['department']} | Shift: {doc['shift_time']}", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w")
        tk.Label(info_box, text=f"Available Days: {doc['available_days']} | Fee: ${float(doc['consultation_fee']):.2f} | Status: {doc['status']}", bg=THEME["bg_card"], fg=THEME["accent_secondary"], font=FONTS["body"]).pack(anchor="w", pady=(2, 0))

        tree = StyledTreeview(
            dialog.body_frame,
            columns=["code", "date", "time", "patient_name", "phone", "reason", "status"],
            headings=["Code", "Date", "Time", "Patient Name", "Phone", "Reason", "Status"],
            widths=[80, 85, 65, 140, 100, 130, 80]
        )
        tree.pack(fill="both", expand=True)

        rows = [
            [a["appointment_code"], str(a["appointment_date"]), str(a["appointment_time"])[:5], a["patient_name"], a["patient_phone"], a["reason"] or "-", a["status"]]
            for a in apps
        ]
        tree.insert_rows(rows)

        ttk.Button(dialog.button_frame, text="Close", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
