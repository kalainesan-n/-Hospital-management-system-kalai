"""
Emergency Management View.
Demonstrates triage prioritization powered by a Python heapq Priority Queue.
Includes academic educational disclaimer and live priority queue dispatching.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
import config
from frontend.components import HeaderBar, StatCard, StyledTreeview, ModalDialog
from backend.emergency_service import EmergencyService, ACADEMIC_DISCLAIMER, SEVERITY_MAPPING
from backend.doctor_service import DoctorService

THEME = config.THEME
FONTS = config.FONTS

class EmergencyView(ttk.Frame):
    """Emergency department triage and heapq priority queue dispatching screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Academic Disclaimer Banner
        banner_frame = tk.Frame(self, bg="#3b1d1d", bd=1, relief="solid", padx=12, pady=8)
        banner_frame.pack(fill="x", pady=(0, 14))

        tk.Label(
            banner_frame,
            text="ACADEMIC & EDUCATIONAL DEMONSTRATION NOTICE",
            bg="#3b1d1d",
            fg=THEME["accent_danger"],
            font=FONTS["body_bold"]
        ).pack(anchor="w")

        tk.Label(
            banner_frame,
            text=ACADEMIC_DISCLAIMER,
            bg="#3b1d1d",
            fg="#fca5a5",
            font=FONTS["caption"],
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=(2, 0))

        # Header
        self.header = HeaderBar(
            self,
            title="Emergency Triage & Priority Queue",
            subtitle="Min-Heap priority queue order (Critical: 1 -> High: 2 -> Medium: 3 -> Low: 4) with FIFO tie-break",
            on_refresh=self.refresh_all
        )
        self.header.pack(fill="x")

        # Triage Severity Count Cards
        cards_frame = ttk.Frame(self, style="TFrame")
        cards_frame.pack(fill="x", pady=(0, 16))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)

        self.card_crit = StatCard(cards_frame, title="Priority 1: Critical", value="--", subtitle="Immediate resuscitation", accent_color=THEME["accent_critical"])
        self.card_crit.grid(row=0, column=0, sticky="nsew", padx=4)

        self.card_high = StatCard(cards_frame, title="Priority 2: High", value="--", subtitle="Emergency intervention", accent_color=THEME["accent_warning"])
        self.card_high.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_med = StatCard(cards_frame, title="Priority 3: Medium", value="--", subtitle="Urgent clinical review", accent_color=THEME["accent_secondary"])
        self.card_med.grid(row=0, column=2, sticky="nsew", padx=4)

        self.card_low = StatCard(cards_frame, title="Priority 4: Low", value="--", subtitle="Non-acute standard care", accent_color=THEME["accent_success"])
        self.card_low.grid(row=0, column=3, sticky="nsew", padx=4)

        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        # View Mode Selector
        tk.Label(toolbar, text="Queue Mode:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.mode_var = tk.StringVar(value="Active Pending Queue (Heap-Sorted)")
        self.mode_cb = ttk.Combobox(toolbar, textvariable=self.mode_var, values=["Active Pending Queue (Heap-Sorted)", "All Historical Cases"], state="readonly", width=32)
        self.mode_cb.pack(side="left", padx=(0, 10))
        self.mode_cb.bind("<<ComboboxSelected>>", lambda e: self.load_cases())

        # Action button to process top priority case
        attend_btn = ttk.Button(toolbar, text="Treat Highest Priority Patient", style="Warning.TButton", command=self.handle_process_next)
        attend_btn.pack(side="left", padx=(0, 8))

        reg_btn = ttk.Button(toolbar, text="+ Register Emergency Case", style="Danger.TButton", command=self.open_register_dialog)
        reg_btn.pack(side="right")

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "code", "rank", "patient", "age", "gender", "severity", "complaint", "vitals", "doctor", "status", "registered"],
            headings=["ID", "Case Code", "Score", "Patient Name", "Age", "Gender", "Triage Severity", "Chief Complaint", "Vitals Summary", "Assigned Doctor", "Status", "Registered At"],
            widths=[45, 80, 50, 130, 45, 65, 110, 180, 140, 130, 85, 120]
        )
        self.table.pack(fill="both", expand=True)

        # Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        update_btn = ttk.Button(action_bar, text="Update Selected Case", style="Secondary.TButton", command=self.open_update_dialog)
        update_btn.pack(side="left", padx=(0, 8))

        self.count_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.count_lbl.pack(side="right")

        self.refresh_all()

    def refresh_all(self):
        self.update_severity_cards()
        self.load_cases()

    def update_severity_cards(self):
        """Refreshes counts across triage levels."""
        try:
            cases = EmergencyService.get_priority_queue_cases()
            c_crit = sum(1 for c in cases if c["triage_severity"] == "Critical")
            c_high = sum(1 for c in cases if c["triage_severity"] == "High")
            c_med = sum(1 for c in cases if c["triage_severity"] == "Medium")
            c_low = sum(1 for c in cases if c["triage_severity"] == "Low")

            self.card_crit.update_value(c_crit)
            self.card_high.update_value(c_high)
            self.card_med.update_value(c_med)
            self.card_low.update_value(c_low)
        except Exception:
            pass

    def load_cases(self):
        """Loads cases into Treeview according to selected mode."""
        try:
            mode = self.mode_var.get()
            if "Active Pending" in mode:
                cases = EmergencyService.get_priority_queue_cases()
            else:
                cases = EmergencyService.get_all_cases()

            rows = [
                [
                    c["emergency_id"],
                    c["case_code"],
                    f"#{c['priority_score']}",
                    c["patient_name"],
                    c["age"],
                    c["gender"],
                    c["triage_severity"],
                    c["chief_complaint"],
                    c["vitals_summary"] or "-",
                    c.get("doctor_name") or "Unassigned",
                    c["status"],
                    str(c["registered_at"])[:16]
                ]
                for c in cases
            ]
            self.table.insert_rows(rows)
            self.count_lbl.configure(text=f"Triage Cases: {len(rows)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load emergency cases: {e}")

    def get_selected_case_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an emergency case from the table.")
            return None
        return int(selected[0])

    def open_register_dialog(self):
        """Opens popup dialog to register an emergency admission."""
        doctors = DoctorService.get_all_doctors(status="Active")

        dialog = ModalDialog(self, title="Register Emergency Triage Case", width=540, height=580)

        # Patient Name
        row_nm = ttk.Frame(dialog.body_frame, style="TFrame")
        row_nm.pack(fill="x", pady=6)
        tk.Label(row_nm, text="Patient Full Name *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        name_var = tk.StringVar()
        ttk.Entry(row_nm, textvariable=name_var).pack(side="left", fill="x", expand=True)

        # Age and Gender
        row_ag = ttk.Frame(dialog.body_frame, style="TFrame")
        row_ag.pack(fill="x", pady=6)
        tk.Label(row_ag, text="Age *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        age_var = tk.StringVar()
        ttk.Entry(row_ag, textvariable=age_var, width=8).pack(side="left", padx=(0, 16))

        tk.Label(row_ag, text="Gender:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 6))
        gender_var = tk.StringVar(value="Male")
        ttk.Combobox(row_ag, textvariable=gender_var, values=["Male", "Female", "Other"], state="readonly", width=10).pack(side="left")

        # Triage Severity (Priority Queue Rank)
        row_sev = ttk.Frame(dialog.body_frame, style="TFrame")
        row_sev.pack(fill="x", pady=6)
        tk.Label(row_sev, text="Triage Severity *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        sev_var = tk.StringVar(value="Critical")
        sev_cb = ttk.Combobox(row_sev, textvariable=sev_var, values=["Critical", "High", "Medium", "Low"], state="readonly")
        sev_cb.pack(side="left", fill="x", expand=True)

        # Chief Complaint
        row_cc = ttk.Frame(dialog.body_frame, style="TFrame")
        row_cc.pack(fill="x", pady=6)
        tk.Label(row_cc, text="Chief Complaint *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        comp_var = tk.StringVar()
        ttk.Entry(row_cc, textvariable=comp_var).pack(side="left", fill="x", expand=True)

        # Vitals Summary
        row_vt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_vt.pack(fill="x", pady=6)
        tk.Label(row_vt, text="Vitals (BP/Pulse/SpO2)", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        vitals_var = tk.StringVar(value="BP 120/80, Pulse 76, SpO2 98%")
        ttk.Entry(row_vt, textvariable=vitals_var).pack(side="left", fill="x", expand=True)

        # Assigned Doctor
        row_doc = ttk.Frame(dialog.body_frame, style="TFrame")
        row_doc.pack(fill="x", pady=6)
        tk.Label(row_doc, text="Attending Doctor", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        doctor_map = {"Unassigned / Triage Desk": None}
        for d in doctors:
            doctor_map[f"{d['full_name']} — {d['specialization']}"] = d['doctor_id']
        doc_options = list(doctor_map.keys())
        doc_var = tk.StringVar(value=doc_options[0])
        ttk.Combobox(row_doc, textvariable=doc_var, values=doc_options, state="readonly").pack(side="left", fill="x", expand=True)

        def save():
            pname = name_var.get().strip()
            complaint = comp_var.get().strip()
            if not pname or not complaint or not age_var.get().strip():
                dialog.show_error("Patient name, age, and chief complaint are required.")
                return

            try:
                age_val = int(age_var.get())
            except ValueError:
                dialog.show_error("Age must be an integer.")
                return

            data = {
                "patient_name": pname,
                "age": age_val,
                "gender": gender_var.get(),
                "triage_severity": sev_var.get(),
                "chief_complaint": complaint,
                "vitals_summary": vitals_var.get().strip(),
                "assigned_doctor_id": doctor_map.get(doc_var.get()),
                "notes": "Admitted via rapid triage intake."
            }

            success, msg, _ = EmergencyService.register_case(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Triage Enqueued", msg)
                self.refresh_all()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Enqueue Case", style="Danger.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def handle_process_next(self):
        """Pops and opens the highest priority emergency patient from the Priority Queue."""
        top_patient = EmergencyService.get_next_patient_to_treat()
        if not top_patient:
            messagebox.showinfo("Queue Empty", "There are currently no pending emergency patients in the queue.")
            return

        self._show_case_processing_dialog(top_patient)

    def open_update_dialog(self):
        """Opens treatment dialog for selected row."""
        case_id = self.get_selected_case_id()
        if not case_id:
            return

        cases = EmergencyService.get_all_cases()
        target = next((c for c in cases if c["emergency_id"] == case_id), None)
        if not target:
            messagebox.showerror("Error", "Case not found.")
            return

        self._show_case_processing_dialog(target)

    def _show_case_processing_dialog(self, case: Dict[str, Any]):
        """Renders processing dialog to transition emergency case status."""
        doctors = DoctorService.get_all_doctors(status="Active")

        dialog = ModalDialog(self, title=f"Emergency Treatment — {case['patient_name']} ({case['case_code']})", width=540, height=480)

        # Case summary banner
        box = tk.Frame(dialog.body_frame, bg=THEME["bg_card"], padx=14, pady=10)
        box.pack(fill="x", pady=(0, 10))
        tk.Label(box, text=f"{case['patient_name']} | {case['gender']}, Age: {case['age']} | Triage Severity: {case['triage_severity']}", bg=THEME["bg_card"], fg=THEME["text_primary"], font=FONTS["subheader"]).pack(anchor="w")
        tk.Label(box, text=f"Complaint: {case['chief_complaint']}", bg=THEME["bg_card"], fg=THEME["accent_warning"], font=FONTS["body_bold"]).pack(anchor="w", pady=(2, 0))
        tk.Label(box, text=f"Vitals: {case.get('vitals_summary') or 'N/A'}", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["caption"]).pack(anchor="w")

        # Status transition
        row_st = ttk.Frame(dialog.body_frame, style="TFrame")
        row_st.pack(fill="x", pady=6)
        tk.Label(row_st, text="Action / Status *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        status_var = tk.StringVar(value="In Progress" if case["status"] == "Pending" else case["status"])
        ttk.Combobox(row_st, textvariable=status_var, values=["In Progress", "Treated", "Admitted", "Transferred"], state="readonly").pack(side="left", fill="x", expand=True)

        # Attending doctor
        row_doc = ttk.Frame(dialog.body_frame, style="TFrame")
        row_doc.pack(fill="x", pady=6)
        tk.Label(row_doc, text="Treating Doctor", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        doc_map = {"Keep Current": None}
        for d in doctors:
            doc_map[f"{d['full_name']} ({d['specialization']})"] = d['doctor_id']
        doc_var = tk.StringVar(value="Keep Current")
        ttk.Combobox(row_doc, textvariable=doc_var, values=list(doc_map.keys()), state="readonly").pack(side="left", fill="x", expand=True)

        # Clinical Notes
        tk.Label(dialog.body_frame, text="Treatment Observations & Intervention Notes:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(anchor="w", pady=(8, 4))
        notes_txt = tk.Text(dialog.body_frame, height=4, bg=THEME["input_bg"], fg=THEME["text_primary"], insertbackground=THEME["text_primary"], relief="solid", bd=1)
        notes_txt.pack(fill="x")
        notes_txt.insert("1.0", f"Treated by emergency staff on shift.")

        def apply_update():
            new_st = status_var.get()
            doctor_id = doc_map.get(doc_var.get())
            notes_val = notes_txt.get("1.0", "end").strip()

            success, msg = EmergencyService.process_case(
                emergency_id=case["emergency_id"],
                new_status=new_st,
                treatment_notes=notes_val,
                doctor_id=doctor_id
            )
            if success:
                dialog.destroy()
                messagebox.showinfo("Updated", msg)
                self.refresh_all()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Save Treatment Update", style="Success.TButton", command=apply_update).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
