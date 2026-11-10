"""
Patient Management View.
Implements full CRUD, search, and integrated medical/appointment/admission history modal.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
from datetime import date
import config
from frontend.components import HeaderBar, SearchBar, StyledTreeview, ModalDialog
from backend.patient_service import PatientService

THEME = config.THEME
FONTS = config.FONTS

class PatientsView(ttk.Frame):
    """Patient registry management screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Patient Management",
            subtitle="Register new patients, view medical profiles, and review past clinical visits",
            on_refresh=self.load_patients
        )
        self.header.pack(fill="x")

        # Action and Search Bar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        self.search_bar = SearchBar(toolbar, placeholder="Search by name, code, phone, or email...", on_search=self.filter_patients)
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_btn = ttk.Button(toolbar, text="+ Add New Patient", style="Success.TButton", command=self.open_add_dialog)
        add_btn.pack(side="right")

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "code", "name", "age", "gender", "phone", "email", "blood_group", "emergency", "created_at"],
            headings=["ID", "Code", "Full Name", "Age", "Gender", "Phone", "Email", "Blood Group", "Emergency Contact", "Registered On"],
            widths=[50, 80, 150, 50, 70, 100, 150, 80, 140, 110]
        )
        self.table.pack(fill="both", expand=True)

        # Bottom Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        view_hist_btn = ttk.Button(action_bar, text="View Medical History", style="TButton", command=self.open_history_dialog)
        view_hist_btn.pack(side="left", padx=(0, 8))

        edit_btn = ttk.Button(action_bar, text="Edit Patient", style="Secondary.TButton", command=self.open_edit_dialog)
        edit_btn.pack(side="left", padx=(0, 8))

        del_btn = ttk.Button(action_bar, text="Delete Patient", style="Danger.TButton", command=self.handle_delete)
        del_btn.pack(side="left")

        self.status_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.status_lbl.pack(side="right")

        self.load_patients()

    def load_patients(self, search_term: Optional[str] = None):
        """Fetches and populates patients into the Treeview."""
        try:
            patients = PatientService.get_all_patients(search_term)
            rows = [
                [
                    p["patient_id"],
                    p["patient_code"],
                    p["full_name"],
                    p["age"] or "-",
                    p["gender"],
                    p["phone"],
                    p["email"] or "-",
                    p["blood_group"] or "-",
                    p["emergency_contact"] or "-",
                    str(p["created_at"])[:10]
                ]
                for p in patients
            ]
            self.table.insert_rows(rows)
            self.status_lbl.configure(text=f"Total Patients: {len(rows)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load patients: {e}")

    def filter_patients(self, term: str):
        self.load_patients(term if term else None)

    def get_selected_patient_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a patient from the list.")
            return None
        return int(selected[0])

    def open_add_dialog(self):
        """Opens popup modal to register a new patient."""
        dialog = ModalDialog(self, title="Register New Patient", width=550, height=650)

        # Form fields
        entries = self._build_patient_form(dialog.body_frame)

        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            # Validation
            if not data["first_name"] or not data["last_name"] or not data["phone"]:
                dialog.show_error("First Name, Last Name, and Phone are required.")
                return

            try:
                age_val = int(data["age"]) if data["age"] else None
            except ValueError:
                dialog.show_error("Age must be a valid number.")
                return

            data["age"] = age_val
            success, msg, _ = PatientService.create_patient(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_patients()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Register Patient", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def open_edit_dialog(self):
        """Opens popup modal to edit existing patient."""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        patient = PatientService.get_patient_by_id(patient_id)
        if not patient:
            messagebox.showerror("Error", "Patient record not found.")
            return

        dialog = ModalDialog(self, title=f"Edit Patient — {patient['patient_code']}", width=550, height=650)
        entries = self._build_patient_form(dialog.body_frame, patient)

        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            if not data["first_name"] or not data["last_name"] or not data["phone"]:
                dialog.show_error("First Name, Last Name, and Phone are required.")
                return

            try:
                age_val = int(data["age"]) if data["age"] else None
            except ValueError:
                dialog.show_error("Age must be a valid number.")
                return

            data["age"] = age_val
            success, msg = PatientService.update_patient(patient_id, data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_patients()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Save Changes", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def _build_patient_form(self, container: ttk.Frame, initial: Optional[Dict[str, Any]] = None) -> Dict[str, tk.StringVar]:
        entries = {}
        fields = [
            ("first_name", "First Name *", initial.get("first_name", "") if initial else ""),
            ("last_name", "Last Name *", initial.get("last_name", "") if initial else ""),
            ("phone", "Phone Number *", initial.get("phone", "") if initial else ""),
            ("email", "Email Address", initial.get("email", "") if initial else ""),
            ("age", "Age", str(initial.get("age", "")) if initial and initial.get("age") else ""),
            ("date_of_birth", "Date of Birth (YYYY-MM-DD)", str(initial.get("date_of_birth", "")) if initial and initial.get("date_of_birth") else ""),
            ("blood_group", "Blood Group", initial.get("blood_group", "") if initial else ""),
            ("emergency_contact", "Emergency Contact (Name & Phone)", initial.get("emergency_contact", "") if initial else ""),
            ("address", "Residential Address", initial.get("address", "") if initial else ""),
            ("medical_history", "Known Allergies & Medical History", initial.get("medical_history", "") if initial else ""),
        ]

        for key, label, val in fields:
            row = ttk.Frame(container, style="TFrame")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=24, anchor="w").pack(side="left")

            if key == "blood_group":
                var = tk.StringVar(value=val or "O+")
                cb = ttk.Combobox(row, textvariable=var, values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], state="readonly", width=25)
                cb.pack(side="left", fill="x", expand=True)
                entries[key] = var
            elif key == "gender":
                pass
            else:
                var = tk.StringVar(value=val)
                ent = ttk.Entry(row, textvariable=var)
                ent.pack(side="left", fill="x", expand=True)
                entries[key] = var

        # Gender radio row
        gender_row = ttk.Frame(container, style="TFrame")
        gender_row.pack(fill="x", pady=4)
        tk.Label(gender_row, text="Gender *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=24, anchor="w").pack(side="left")
        gender_var = tk.StringVar(value=initial.get("gender", "Male") if initial else "Male")
        for g in ["Male", "Female", "Other"]:
            rb = tk.Radiobutton(
                gender_row, text=g, value=g, variable=gender_var,
                bg=THEME["bg_dark"], fg=THEME["text_primary"],
                selectcolor=THEME["bg_card"], activebackground=THEME["bg_dark"]
            )
            rb.pack(side="left", padx=4)
        entries["gender"] = gender_var

        return entries

    def handle_delete(self):
        """Deletes selected patient after confirmation."""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            "Are you sure you want to delete this patient record?\nThis action cannot be undone."
        )
        if not confirm:
            return

        success, msg = PatientService.delete_patient(patient_id)
        if success:
            messagebox.showinfo("Deleted", msg)
            self.load_patients()
        else:
            messagebox.showerror("Error", msg)

    def open_history_dialog(self):
        """Displays full patient clinical profile and past visit history."""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            return

        hist = PatientService.get_patient_history(patient_id)
        patient = hist["patient"]
        if not patient:
            messagebox.showerror("Error", "Patient details could not be retrieved.")
            return

        dialog = ModalDialog(self, title=f"Medical History — {patient['first_name']} {patient['last_name']} ({patient['patient_code']})", width=750, height=620)

        # Patient Header Summary
        info_box = tk.Frame(dialog.body_frame, bg=THEME["bg_card"], padx=14, pady=12)
        info_box.pack(fill="x", pady=(0, 14))

        tk.Label(info_box, text=f"{patient['first_name']} {patient['last_name']} | {patient['gender']}, Age: {patient['age'] or 'N/A'} | Blood Group: {patient['blood_group'] or 'N/A'}", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w")
        tk.Label(info_box, text=f"Phone: {patient['phone']} | Emergency Contact: {patient['emergency_contact'] or 'None'}", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body"]).pack(anchor="w", pady=(2, 2))
        tk.Label(info_box, text=f"Medical History / Chronic Conditions: {patient['medical_history'] or 'None recorded'}", bg=THEME["bg_card"], fg=THEME["accent_warning"], font=FONTS["body"]).pack(anchor="w")

        # Tabbed Notebook for Appointments and Admissions
        notebook = ttk.Notebook(dialog.body_frame)
        notebook.pack(fill="both", expand=True)

        # Tab 1: Appointments History
        app_tab = ttk.Frame(notebook, style="TFrame", padding=10)
        notebook.add(app_tab, text=f"Appointments ({len(hist['appointments'])})")

        app_tree = StyledTreeview(
            app_tab,
            columns=["code", "date", "time", "doctor", "specialization", "reason", "status"],
            headings=["Code", "Date", "Time", "Doctor", "Specialization", "Reason", "Status"],
            widths=[80, 80, 60, 130, 120, 140, 80]
        )
        app_tree.pack(fill="both", expand=True)
        app_rows = [
            [a["appointment_code"], str(a["appointment_date"]), str(a["appointment_time"])[:5], a["doctor_name"], a["specialization"], a["reason"] or "-", a["status"]]
            for a in hist["appointments"]
        ]
        app_tree.insert_rows(app_rows)

        # Tab 2: Hospital Admissions History
        adm_tab = ttk.Frame(notebook, style="TFrame", padding=10)
        notebook.add(adm_tab, text=f"Admissions ({len(hist['admissions'])})")

        adm_tree = StyledTreeview(
            adm_tab,
            columns=["code", "admitted", "discharged", "bed", "ward", "doctor", "diagnosis", "status"],
            headings=["Code", "Admission Date", "Discharge Date", "Bed", "Ward", "Doctor", "Diagnosis", "Status"],
            widths=[80, 110, 110, 70, 100, 120, 130, 80]
        )
        adm_tree.pack(fill="both", expand=True)
        adm_rows = [
            [adm["admission_code"], str(adm["admission_date"])[:16], str(adm["discharge_date"])[:16] if adm["discharge_date"] else "Active", adm["bed_number"], adm["ward_name"], adm["doctor_name"], adm["diagnosis"], adm["status"]]
            for adm in hist["admissions"]
        ]
        adm_tree.insert_rows(adm_rows)

        ttk.Button(dialog.button_frame, text="Close", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
