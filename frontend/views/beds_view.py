"""
Bed Management View.
Monitors ward occupancy, bed types, live allocation states, and prevents double allocation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List
import config
from frontend.components import HeaderBar, StatCard, StyledTreeview, ModalDialog
from backend.bed_service import BedService

THEME = config.THEME
FONTS = config.FONTS

class BedsView(ttk.Frame):
    """Inpatient bed inventory and ward management screen."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Bed Management",
            subtitle="Monitor ward capacity, allocate beds to patients, and ensure atomic double-allocation protection",
            on_refresh=self.refresh_all
        )
        self.header.pack(fill="x")

        # Top Summary Cards (4 cards)
        cards_frame = ttk.Frame(self, style="TFrame")
        cards_frame.pack(fill="x", pady=(0, 16))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)

        self.card_total = StatCard(cards_frame, title="Total Beds", value="--", subtitle="Hospital-wide", accent_color=THEME["accent_primary"])
        self.card_total.grid(row=0, column=0, sticky="nsew", padx=4)

        self.card_available = StatCard(cards_frame, title="Available Beds", value="--", subtitle="Ready for admission", accent_color=THEME["accent_success"])
        self.card_available.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_occupied = StatCard(cards_frame, title="Occupied Beds", value="--", subtitle="Currently admitted", accent_color=THEME["accent_danger"])
        self.card_occupied.grid(row=0, column=2, sticky="nsew", padx=4)

        self.card_maintenance = StatCard(cards_frame, title="Under Maintenance", value="--", subtitle="Cleaning / sanitization", accent_color=THEME["accent_warning"])
        self.card_maintenance.grid(row=0, column=3, sticky="nsew", padx=4)

        # Toolbar
        toolbar = ttk.Frame(self, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 12))

        # Ward Filter
        tk.Label(toolbar, text="Ward:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.ward_var = tk.StringVar(value="All")
        self.ward_cb = ttk.Combobox(toolbar, textvariable=self.ward_var, state="readonly", width=18)
        self.ward_cb.pack(side="left", padx=(0, 10))
        self.ward_cb.bind("<<ComboboxSelected>>", lambda e: self.load_beds())

        # Type Filter
        tk.Label(toolbar, text="Type:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.type_var = tk.StringVar(value="All")
        self.type_cb = ttk.Combobox(toolbar, textvariable=self.type_var, values=["All", "General", "Semi-Private", "Private", "ICU", "Emergency"], state="readonly", width=14)
        self.type_cb.pack(side="left", padx=(0, 10))
        self.type_cb.bind("<<ComboboxSelected>>", lambda e: self.load_beds())

        # Status Filter
        tk.Label(toolbar, text="Status:", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(side="left", padx=(0, 4))
        self.status_var = tk.StringVar(value="All")
        self.status_cb = ttk.Combobox(toolbar, textvariable=self.status_var, values=["All", "Available", "Occupied", "Maintenance"], state="readonly", width=12)
        self.status_cb.pack(side="left", padx=(0, 10))
        self.status_cb.bind("<<ComboboxSelected>>", lambda e: self.load_beds())

        add_btn = ttk.Button(toolbar, text="+ Add New Bed", style="Success.TButton", command=self.open_add_dialog)
        add_btn.pack(side="right")

        # Table
        self.table = StyledTreeview(
            self,
            columns=["id", "number", "ward", "type", "charge", "status", "notes"],
            headings=["ID", "Bed Number", "Ward Name", "Bed Type", "Daily Rate ($)", "Occupancy Status", "Facility Details"],
            widths=[45, 100, 160, 120, 100, 120, 220]
        )
        self.table.pack(fill="both", expand=True)

        # Action Bar
        action_bar = ttk.Frame(self, style="TFrame", padding=(0, 10, 0, 0))
        action_bar.pack(fill="x")

        release_btn = ttk.Button(action_bar, text="Release Bed (To Available)", style="Success.TButton", command=self.handle_release_bed)
        release_btn.pack(side="left", padx=(0, 8))

        maint_btn = ttk.Button(action_bar, text="Set Under Maintenance", style="Warning.TButton", command=self.handle_set_maintenance)
        maint_btn.pack(side="left", padx=(0, 8))

        del_btn = ttk.Button(action_bar, text="Delete Bed", style="Danger.TButton", command=self.handle_delete)
        del_btn.pack(side="left")

        self.count_lbl = tk.Label(action_bar, text="", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["caption"])
        self.count_lbl.pack(side="right")

        self.refresh_all()

    def refresh_all(self):
        self.update_summary_cards()
        self.load_wards()
        self.load_beds()

    def update_summary_cards(self):
        """Pulls bed summary across wards."""
        try:
            summary = BedService.get_ward_summary()
            total = sum(s["total_beds"] for s in summary)
            avail = sum(s["available_beds"] for s in summary)
            occ = sum(s["occupied_beds"] for s in summary)
            maint = sum(s["maintenance_beds"] for s in summary)

            self.card_total.update_value(total)
            self.card_available.update_value(avail)
            self.card_occupied.update_value(occ)
            self.card_maintenance.update_value(maint)
        except Exception:
            pass

    def load_wards(self):
        try:
            summary = BedService.get_ward_summary()
            ward_names = [s["ward_name"] for s in summary]
            self.ward_cb.configure(values=["All"] + ward_names)
        except Exception:
            pass

    def load_beds(self):
        """Loads beds according to filter criteria."""
        try:
            ward = self.ward_var.get()
            btype = self.type_var.get()
            status = self.status_var.get()
            beds = BedService.get_all_beds(ward, btype, status)
            rows = [
                [
                    b["bed_id"],
                    b["bed_number"],
                    b["ward_name"],
                    b["bed_type"],
                    f"${float(b['daily_charge']):.2f}",
                    b["status"],
                    b["notes"] or "-"
                ]
                for b in beds
            ]
            self.table.insert_rows(rows)
            self.count_lbl.configure(text=f"Total Displayed Beds: {len(rows)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load beds: {e}")

    def get_selected_bed_id(self) -> Optional[int]:
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a bed from the table.")
            return None
        return int(selected[0])

    def open_add_dialog(self):
        """Opens popup dialog to register a new bed."""
        dialog = ModalDialog(self, title="Register New Hospital Bed", width=480, height=480)

        # Bed number
        row_num = ttk.Frame(dialog.body_frame, style="TFrame")
        row_num.pack(fill="x", pady=6)
        tk.Label(row_num, text="Bed Number *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        num_var = tk.StringVar()
        ttk.Entry(row_num, textvariable=num_var).pack(side="left", fill="x", expand=True)

        # Ward name
        row_wd = ttk.Frame(dialog.body_frame, style="TFrame")
        row_wd.pack(fill="x", pady=6)
        tk.Label(row_wd, text="Ward Name *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        ward_var = tk.StringVar(value="General Ward A")
        ward_cb = ttk.Combobox(row_wd, textvariable=ward_var, values=["Intensive Care Unit", "Emergency Ward", "General Ward A", "General Ward B", "Private Deluxe Wing", "Semi-Private Ward"])
        ward_cb.pack(side="left", fill="x", expand=True)

        # Bed Type
        row_tp = ttk.Frame(dialog.body_frame, style="TFrame")
        row_tp.pack(fill="x", pady=6)
        tk.Label(row_tp, text="Bed Type *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        type_var = tk.StringVar(value="General")
        ttk.Combobox(row_tp, textvariable=type_var, values=["General", "Semi-Private", "Private", "ICU", "Emergency"], state="readonly").pack(side="left", fill="x", expand=True)

        # Daily Charge
        row_ch = ttk.Frame(dialog.body_frame, style="TFrame")
        row_ch.pack(fill="x", pady=6)
        tk.Label(row_ch, text="Daily Charge ($) *", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        charge_var = tk.StringVar(value="600.00")
        ttk.Entry(row_ch, textvariable=charge_var).pack(side="left", fill="x", expand=True)

        # Notes
        row_nt = ttk.Frame(dialog.body_frame, style="TFrame")
        row_nt.pack(fill="x", pady=6)
        tk.Label(row_nt, text="Facility Notes", bg=THEME["bg_dark"], fg=THEME["text_secondary"], font=FONTS["body_bold"], width=18, anchor="w").pack(side="left")
        notes_var = tk.StringVar()
        ttk.Entry(row_nt, textvariable=notes_var).pack(side="left", fill="x", expand=True)

        def save():
            num = num_var.get().strip().upper()
            ward = ward_var.get().strip()
            if not num or not ward:
                dialog.show_error("Bed number and ward name are required.")
                return

            try:
                charge = float(charge_var.get())
            except ValueError:
                dialog.show_error("Daily charge must be a valid number.")
                return

            data = {
                "bed_number": num,
                "ward_name": ward,
                "bed_type": type_var.get(),
                "daily_charge": charge,
                "status": "Available",
                "notes": notes_var.get().strip()
            }

            success, msg, _ = BedService.create_bed(data)
            if success:
                dialog.destroy()
                messagebox.showinfo("Success", msg)
                self.refresh_all()
            else:
                dialog.show_error(msg)

        ttk.Button(dialog.button_frame, text="Create Bed", style="Success.TButton", command=save).pack(side="right", padx=(8, 0))
        ttk.Button(dialog.button_frame, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")

    def handle_release_bed(self):
        """Releases bed to Available state."""
        bed_id = self.get_selected_bed_id()
        if not bed_id:
            return

        success, msg = BedService.release_bed(bed_id)
        if success:
            messagebox.showinfo("Success", msg)
            self.refresh_all()
        else:
            messagebox.showerror("Error", msg)

    def handle_set_maintenance(self):
        """Sets selected bed under maintenance."""
        bed_id = self.get_selected_bed_id()
        if not bed_id:
            return

        bed = BedService.get_bed_by_id(bed_id)
        if not bed:
            return
        if bed["status"] == "Occupied":
            messagebox.showwarning("Blocked", "Cannot place an occupied bed under maintenance. Discharge patient first.")
            return

        bed["status"] = "Maintenance"
        success, msg = BedService.update_bed(bed_id, bed)
        if success:
            messagebox.showinfo("Status Updated", f"Bed {bed['bed_number']} marked as Under Maintenance.")
            self.refresh_all()
        else:
            messagebox.showerror("Error", msg)

    def handle_delete(self):
        """Deletes selected bed after verifying no admission linkages."""
        bed_id = self.get_selected_bed_id()
        if not bed_id:
            return

        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this bed from inventory?")
        if not confirm:
            return

        success, msg = BedService.delete_bed(bed_id)
        if success:
            messagebox.showinfo("Removed", msg)
            self.refresh_all()
        else:
            messagebox.showerror("Error", msg)
