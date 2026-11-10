"""
Admission and Discharge View.
Manages patient in-patient hospitalizations, bed assignments, and automatic bed releasing on discharge.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
from datetime import datetime
import config
from frontend.components import HeaderBar, SearchBar, StyledTreeview, ModalDialog
from backend.admission_service import AdmissionService
from backend.patient_service import PatientService
from backend.doctor_service import DoctorService
from backend.bed_service import BedService

THEME = config.THEME
FONTS = config.FONTS

class AdmissionsView(ttk.Frame):
    """Hospital inpatient admissions and discharge management screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Admission & Discharge Management",
            subtitle="Admit in-patients, assign available beds, and perform automated bed release upon discharge",
            on_refresh=self.load_admissions
        )
        self.header.pack(fill="x")

        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        self.search_bar = SearchBar(toolbar, placeholder="Search admission by patient, bed, or diagnosis...", on_search=self.filter_admissions)
        self.search_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Status Filter
        tk.Label(toolbar, text="Status:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.status_var = tk.StringVar(value="All")
        self.status_cb = ttk.Combobox(toolbar, textvariable=self.status_var, values=["All", "Admitted", "Discharged"], state="readonly", width=12)
        self.status_cb.pack(side="left", padx=(0, 10))
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self.filter_admissions(self.search_bar.get()))

        admit_btn = ttk.Button(toolbar, text="+ Admit Patient", style="Success.TButton", command=self.open_admit_dialog)
        admit_btn.pack(side="right")

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "code", "patient", "bed", "ward", "doctor", "admit_dt", "discharge_dt", "type", "diagnosis", "status", "bill"],
            headings=["ID", "Code", "Patient Name", "Bed", "Ward", "Attending Doctor", "Admitted At", "Discharged At", "Type", "Diagnosis", "Status", "Total ($)"],
            widths=[45, 80, 140, 70, 110, 130, 110, 110, 80, 140, 80, 80]
        )
        self.table.pack(fill="both", expand=True)

        # Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        discharge_btn = ttk.Button(action_bar, text="Discharge Patient (Release Bed)", style="Warning.TButton", command=self.open_discharge_dialog)
        discharge_btn.pack(side="left", padx=(0, 8))

        view_btn = ttk.Button(action_bar, text="View Admission Details", style="Secondary.TButton", command=self.open_details_dialog)
        view_btn.pack(side="left")

        self.count_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.count_lbl.pack(side="right")

        self.load_admissions()

    def load_admissions(self, search_term: Optional[str] = None):
        """Fetches and displays hospital admissions."""
        try:
            status = self.status_var.get()
            admissions = AdmissionService.get_all_admissions(search_term, status)
            rows = [
                [
                    adm["admission_id"],
                    adm["admission_code"],
                    adm["patient_name"],
                    adm["bed_number"],
                    adm["ward_name"],
                    adm["doctor_name"],
                    str(adm["admission_date"])[:16],
                    str(adm["discharge_date"])[:16] if adm["discharge_date"] else "Active",
                    adm["admission_type"],
                    adm["diagnosis"],
                    adm["status"],
                    f"${float(adm['total_amount'] or 0):.2f}"
                ]
                for adm in admissions
            ]
            self.table.insert_rows(rows)
            self.count_lbl.configure(text=f"Total Admissions: {len(rows)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load admissions: {e}")

    def filter_admissions(self, term: str):
        self.load_admissions(term if term else None)

    def get_selected_admission_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an admission record from the table.")
            return None
        return int(selected[0])

    def open_admit_dialog(self):
        """Opens admission dialog with patient, available bed, and doctor selectors."""
        patients = PatientService.get_all_patients()
        available_beds = BedService.get_available_beds()
        doctors = DoctorService.get_all_doctors(status="Active")

        if not patients:
            messagebox.showwarning("Notice", "Please register at least one patient first.")
            return
        if not available_beds:
            messagebox.showerror("No Beds Available", "All hospital beds are currently occupied or under maintenance. Cannot admit patient.")
            return
        if not doctors:
            messagebox.showwarning("Notice", "No active doctors available.")
            return

        dialog = ModalDialog(self, title="Admit Patient to Hospital", width=560, height=580)

        # Patient Dropdown
        row_pat = ttk.Frame(dialog.body_frame, style="TFrame")
        row_pat.pack(fill="x", pady=6)
        tk.Label(row_pat, text="Patient *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        patient_map = {f"[{p['patient_code']}] {p['full_name']}": p['patient_id'] for p in patients}
        patient_options = list(patient_map.keys())
        patient_var = tk.StringVar(value=patient_options[0])
        pat_cb = ttk.Combobox(row_pat, textvariable=patient_var, values=patient_options, state="readonly")
        pat_cb.pack(side="left", fill="x", expand=True)

        # Available Bed Dropdown
        row_bed = ttk.Frame(dialog.body_frame, style="TFrame")
        row_bed.pack(fill="x", pady=6)
        tk.Label(row_bed, text="Assign Bed *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        bed_map = {f"{b['bed_number']} — {b['ward_name']} ({b['bed_type']} - ${float(b['daily_charge']):.0f}/day)": b['bed_id'] for b in available_beds}
        bed_options = list(bed_map.keys())
        bed_var = tk.StringVar(value=bed_options[0])
        bed_cb = ttk.Combobox(row_bed, textvariable=bed_var, values=bed_options, state="readonly")
        bed_cb.pack(side="left", fill="x", expand=True)

        # Attending Doctor Dropdown
        row_doc = ttk.Frame(dialog.body_frame, style="TFrame")
        row_doc.pack(fill="x", pady=6)
        tk.Label(row_doc, text="Attending Doctor *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        doctor_map = {f"{d['full_name']} — {d['specialization']}": d['doctor_id'] for d in doctors}
        doctor_options = list(doctor_map.keys())
        doctor_var = tk.StringVar(value=doctor_options[0])
        doc_cb = ttk.Combobox(row_doc, textvariable=doctor_var, values=doctor_options, state="readonly")
        doc_cb.pack(side="left", fill="x", expand=True)

        # Admission Type
        row_tp = ttk.Frame(dialog.body_frame, style="TFrame")
        row_tp.pack(fill="x", pady=6)
        tk.Label(row_tp, text="Admission Type *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        type_var = tk.StringVar(value="Routine")
        ttk.Combobox(row_tp, textvariable=type_var, values=["Routine", "Emergency", "Urgent"], state="readonly").pack(side="left", fill="x", expand=True)

        # Primary Diagnosis
        row_dg = ttk.Frame(dialog.body_frame, style="TFrame")
        row_dg.pack(fill="x", pady=6)
        tk.Label(row_dg, text="Clinical Diagnosis *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        diagnosis_var = tk.StringVar()
        ttk.Entry(row_dg, textvariable=diagnosis_var).pack(side="left", fill="x", expand=True)

        # Initial Deposit / Fee
        row_amt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_amt.pack(fill="x", pady=6)
        tk.Label(row_amt, text="Deposit Amount ($)", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        amt_var = tk.StringVar(value="1000.00")
        ttk.Entry(row_amt, textvariable=amt_var).pack(side="left", fill="x", expand=True)

        def admit():
            pid = patient_map.get(patient_var.get())
            bid = bed_map.get(bed_var.get())
            did = doctor_map.get(doctor_var.get())
            diag = diagnosis_var.get().strip()

            if not diag:
                dialog.show_error("Please specify clinical diagnosis.")
                return

            try:
                amt = float(amt_var.get()) if amt_var.get() else 0.0
            except ValueError:
                dialog.show_error("Deposit amount must be a number.")
                return

            data = {
                "patient_id": pid,
                "bed_id": bid,
                "doctor_id": did,
                "diagnosis": diag,
                "admission_type": type_var.get(),
                "total_amount": amt
            }

            success, msg, _ = AdmissionService.admit_patient(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_admissions()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Confirm Admission", style="Success.TButton", command=admit).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def open_discharge_dialog(self):
        """Opens discharge dialog with summary, final bill calculation, and automatic bed release."""
        admission_id = self.get_selected_admission_id()
        if not admission_id:
            return

        adm = AdmissionService.get_admission_by_id(admission_id)
        if not adm:
            messagebox.showerror("Error", "Admission record not found.")
            return
        if adm["status"] == "Discharged":
            messagebox.showinfo("Already Discharged", "This patient has already been discharged.")
            return

        dialog = ModalDialog(self, title=f"Discharge Patient — {adm['patient_name']} ({adm['admission_code']})", width=540, height=520)

        info_box = tk.Frame(dialog.body_frame, bg=THEME["bg_card"], padx=14, pady=10)
        info_box.pack(fill="x", pady=(0, 10))
        tk.Label(info_box, text=f"Patient: {adm['patient_name']} | Bed: {adm['bed_number']} ({adm['ward_name']})", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w")
        tk.Label(info_box, text=f"Admitted: {str(adm['admission_date'])[:16]} | Doctor: {adm['doctor_name']}", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body"]).pack(anchor="w", pady=(2, 0))

        # Discharge Summary
        tk.Label(dialog.body_frame, text="Discharge Summary & Medical Advice *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(anchor="w", pady=(8, 4))
        summary_txt = tk.Text(dialog.body_frame, height=5, bg=THEME["input_bg"], fg=THEME["text_primary"], insertbackground=THEME["text_primary"], relief="solid", bd=1)
        summary_txt.pack(fill="x")
        summary_txt.insert("1.0", "Patient has recovered satisfactorily and is medically stable for discharge. Continue prescribed medications.")

        # Total Final Bill
        row_bill = ttk.Frame(dialog.body_frame, style="TFrame")
        row_bill.pack(fill="x", pady=(12, 6))
        tk.Label(row_bill, text="Final Billed Amount ($)", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=22, anchor="w").pack(side="left")
        current_amt = float(adm.get("total_amount") or 5000.0)
        bill_var = tk.StringVar(value=f"{current_amt:.2f}")
        ttk.Entry(row_bill, textvariable=bill_var).pack(side="left", fill="x", expand=True)

        # Release bed notice
        tk.Label(
            dialog.body_frame,
            text=f"* Bed {adm['bed_number']} in {adm['ward_name']} will automatically be released to Available status upon discharge.",
            bg=THEME["bg_dark"],
            fg=THEME["accent_success"],
            font=FONTS["caption"],
            wraplength=480
        ).pack(anchor="w", pady=(10, 0))

        def discharge():
            summ = summary_txt.get("1.0", "end").strip()
            if not summ:
                dialog.show_error("Discharge summary is required.")
                return

            try:
                final_bill = float(bill_var.get())
            except ValueError:
                dialog.show_error("Final bill amount must be a number.")
                return

            success, msg = AdmissionService.discharge_patient(
                admission_id=admission_id,
                discharge_summary=summ,
                total_amount=final_bill
            )
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.load_admissions()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Confirm Discharge & Release Bed", style="Success.TButton", command=discharge).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def open_details_dialog(self):
        """Displays full read-only admission record."""
        admission_id = self.get_selected_admission_id()
        if not admission_id:
            return

        adm = AdmissionService.get_admission_by_id(admission_id)
        if not adm:
            messagebox.showerror("Error", "Record not found.")
            return

        dialog = ModalDialog(self, title=f"Admission Record — {adm['admission_code']}", width=540, height=480)

        details = [
            ("Admission Code", adm["admission_code"]),
            ("Patient Name", f"{adm['patient_name']} ({adm['patient_code']})"),
            ("Bed Number & Ward", f"{adm['bed_number']} — {adm['ward_name']}"),
            ("Attending Doctor", adm["doctor_name"]),
            ("Admission Date", str(adm["admission_date"])),
            ("Discharge Date", str(adm["discharge_date"]) if adm["discharge_date"] else "Still Admitted"),
            ("Admission Type", adm["admission_type"]),
            ("Current Status", adm["status"]),
            ("Diagnosis", adm["diagnosis"]),
            ("Discharge Summary", adm["discharge_summary"] or "N/A"),
            ("Total Billed Amount", f"${float(adm['total_amount'] or 0):.2f}"),
        ]

        for label, val in details:
            row = ttk.Frame(dialog.body_frame, style="TFrame")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=f"{label}:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=20, anchor="w").pack(side="left")
            tk.Label(row, text=str(val), bg=THEME["bg_dark"], fg=THEME["text_primary"], font=FONTS["body"], wraplength=300, justify="left").pack(side="left", fill="x", expand=True)

        ttk.Button(dialog.button_frame, text="Close", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
