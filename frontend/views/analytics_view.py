"""
Analytics View.
Embeds Matplotlib charts directly inside Tkinter tabs using FigureCanvasTkAgg,
rendering real-time statistical insights processed by Pandas and NumPy.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np

import config
from frontend.components import HeaderBar
from backend.analytics_service import AnalyticsService

THEME = config.THEME
FONTS = config.FONTS

class AnalyticsView(ttk.Frame):
    """Visual analytics dashboard embedding high-resolution Matplotlib figures."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", padding=20, **kwargs)

        # Header
        self.header = HeaderBar(
            self,
            title="Hospital Intelligence & Analytics",
            subtitle="Pandas statistical aggregations rendered through embedded Matplotlib charts",
            on_refresh=self.render_all_charts
        )
        self.header.pack(fill="x")

        # Tabbed Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Clinical Operations & Doctor Workload
        self.tab1 = ttk.Frame(self.notebook, style="TFrame", padding=10)
        self.notebook.add(self.tab1, text="Clinical Operations & Doctors")

        # Tab 2: Bed Capacity & Admissions
        self.tab2 = ttk.Frame(self.notebook, style="TFrame", padding=10)
        self.notebook.add(self.tab2, text="Bed Capacity & Inpatient Flow")

        # Tab 3: Emergency Triage & Registrations
        self.tab3 = ttk.Frame(self.notebook, style="TFrame", padding=10)
        self.notebook.add(self.tab3, text="Emergency Triage & Patient Trends")

        # Canvases storage
        self.canvases = []

        self.render_all_charts()

    def _style_figure(self, fig: Figure):
        """Applies dark theme palette to Matplotlib figures."""
        fig.patch.set_facecolor(THEME["bg_card"])

    def _style_axis(self, ax):
        """Applies dark theme palette to Matplotlib axes, ticks, and grids."""
        ax.set_facecolor(THEME["bg_card"])
        ax.tick_params(colors=THEME["text_secondary"], labelsize=9)
        ax.xaxis.label.set_color(THEME["text_primary"])
        ax.yaxis.label.set_color(THEME["text_primary"])
        ax.title.set_color(THEME["text_primary"])
        for spine in ax.spines.values():
            spine.set_color(THEME["border_color"])
        ax.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")

    def render_all_charts(self):
        """Re-computes metrics via Pandas and redraws all charts across tabs."""
        # Clean up existing canvases
        for c in self.canvases:
            c.get_tk_widget().destroy()
        self.canvases.clear()

        self._render_tab1()
        self._render_tab2()
        self._render_tab3()

    def _render_tab1(self):
        """Tab 1: Doctor Workload Bar Chart + Appointment Status Donut Chart."""
        fig = Figure(figsize=(10, 5), dpi=95)
        self._style_figure(fig)

        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        self._style_axis(ax1)
        self._style_axis(ax2)

        # Chart 1: Doctor Workload
        df_docs = AnalyticsService.get_doctor_workload_stats()
        if not df_docs.empty:
            names = [name.replace("Dr. ", "") for name in df_docs["doctor_name"]]
            x = np.arange(len(names))
            width = 0.35
            ax1.bar(x - width/2, df_docs["total_appointments"], width, label="Total Bookings", color=THEME["accent_primary"])
            ax1.bar(x + width/2, df_docs["completed_appointments"], width, label="Completed", color=THEME["accent_success"])
            ax1.set_xticks(x)
            ax1.set_xticklabels(names, rotation=25, ha="right", fontsize=8)
            ax1.set_title("Doctor Consultation Workload", fontsize=11, fontweight="bold")
            ax1.set_ylabel("Number of Appointments")
            leg = ax1.legend(facecolor=THEME["bg_dark"], edgecolor=THEME["border_color"], fontsize=8)
            for text in leg.get_texts():
                text.set_color(THEME["text_primary"])
        else:
            ax1.text(0.5, 0.5, "No appointment data available", ha="center", va="center", color=THEME["text_muted"])

        # Chart 2: Appointment Status Donut
        df_status = AnalyticsService.get_appointment_status_distribution()
        if not df_status.empty:
            colors = [THEME["accent_primary"], THEME["accent_success"], THEME["accent_danger"], THEME["accent_warning"]]
            wedges, texts, autotexts = ax2.pie(
                df_status["count"],
                labels=df_status["status"],
                autopct="%1.1f%%",
                startangle=140,
                colors=colors[:len(df_status)],
                wedgeprops=dict(width=0.45, edgecolor=THEME["bg_card"], linewidth=2)
            )
            for t in texts:
                t.set_color(THEME["text_primary"])
                t.set_fontsize(9)
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_fontsize(8)
                at.set_weight("bold")
            ax2.set_title("Appointment Status Breakdown", fontsize=11, fontweight="bold")
        else:
            ax2.text(0.5, 0.5, "No appointment records", ha="center", va="center", color=THEME["text_muted"])

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=self.tab1)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases.append(canvas)

    def _render_tab2(self):
        """Tab 2: Ward Bed Occupancy Breakdown + Inpatient Admission Types."""
        fig = Figure(figsize=(10, 5), dpi=95)
        self._style_figure(fig)

        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        self._style_axis(ax1)
        self._style_axis(ax2)

        # Chart 1: Bed Occupancy by Ward
        df_beds = AnalyticsService.get_bed_occupancy_by_ward()
        if not df_beds.empty:
            wards = [w[:14] for w in df_beds["ward_name"]]
            x = np.arange(len(wards))
            ax1.bar(x, df_beds["occupied"], label="Occupied", color=THEME["accent_danger"], width=0.5)
            ax1.bar(x, df_beds["available"], bottom=df_beds["occupied"], label="Available", color=THEME["accent_success"], width=0.5)
            ax1.set_xticks(x)
            ax1.set_xticklabels(wards, rotation=30, ha="right", fontsize=8)
            ax1.set_title("Bed Capacity & Status by Ward", fontsize=11, fontweight="bold")
            ax1.set_ylabel("Total Beds")
            leg = ax1.legend(facecolor=THEME["bg_dark"], edgecolor=THEME["border_color"], fontsize=8)
            for text in leg.get_texts():
                text.set_color(THEME["text_primary"])
        else:
            ax1.text(0.5, 0.5, "No bed data", ha="center", va="center", color=THEME["text_muted"])

        # Chart 2: Admission Types & Discharge
        df_adm = AnalyticsService.get_admission_discharge_comparison()
        if not df_adm.empty:
            types = df_adm["admission_type"]
            x = np.arange(len(types))
            width = 0.35
            ax2.bar(x - width/2, df_adm["active_admissions"], width, label="Currently Admitted", color="#8b5cf6")
            ax2.bar(x + width/2, df_adm["discharged_cases"], width, label="Discharged", color=THEME["accent_secondary"])
            ax2.set_xticks(x)
            ax2.set_xticklabels(types, fontsize=9)
            ax2.set_title("Inpatient Flow by Admission Type", fontsize=11, fontweight="bold")
            ax2.set_ylabel("Patients")
            leg = ax2.legend(facecolor=THEME["bg_dark"], edgecolor=THEME["border_color"], fontsize=8)
            for text in leg.get_texts():
                text.set_color(THEME["text_primary"])
        else:
            ax2.text(0.5, 0.5, "No admission data", ha="center", va="center", color=THEME["text_muted"])

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=self.tab2)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases.append(canvas)

    def _render_tab3(self):
        """Tab 3: Emergency Triage Severity Frequency + Patient Registrations Trend."""
        fig = Figure(figsize=(10, 5), dpi=95)
        self._style_figure(fig)

        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)
        self._style_axis(ax1)
        self._style_axis(ax2)

        # Chart 1: Emergency Severity Distribution
        df_emg = AnalyticsService.get_emergency_severity_stats()
        if not df_emg.empty:
            sev_colors = {
                "Critical": THEME["accent_critical"],
                "High": THEME["accent_warning"],
                "Medium": THEME["accent_secondary"],
                "Low": THEME["accent_success"]
            }
            colors = [sev_colors.get(s, THEME["accent_primary"]) for s in df_emg["triage_severity"]]
            bars = ax1.bar(df_emg["triage_severity"], df_emg["total_cases"], color=colors, width=0.55)
            ax1.set_title("Emergency Cases by Triage Priority", fontsize=11, fontweight="bold")
            ax1.set_ylabel("Number of Emergency Cases")

            # Value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(
                    f"{int(height)}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    color=THEME["text_primary"],
                    fontsize=9,
                    fontweight="bold"
                )
        else:
            ax1.text(0.5, 0.5, "No emergency triage records", ha="center", va="center", color=THEME["text_muted"])

        # Chart 2: Daily Patient Registrations Trend
        df_reg = AnalyticsService.get_patient_registration_stats()
        if not df_reg.empty:
            dates = [d.strftime("%m-%d") for d in df_reg["reg_date"]]
            ax2.plot(dates, df_reg["count"], marker="o", color=THEME["accent_secondary"], linewidth=2, markersize=5)
            ax2.fill_between(range(len(dates)), df_reg["count"], color=THEME["accent_secondary"], alpha=0.15)
            ax2.set_title("Patient Registration Trajectory", fontsize=11, fontweight="bold")
            ax2.set_ylabel("New Patients Registered")
            ax2.set_xticks(range(len(dates)))
            ax2.set_xticklabels(dates, rotation=35, ha="right", fontsize=8)
        else:
            ax2.text(0.5, 0.5, "No registration history", ha="center", va="center", color=THEME["text_muted"])

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=self.tab3)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases.append(canvas)
