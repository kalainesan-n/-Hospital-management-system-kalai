"""
Login View.
Provides administrative login screen with input validation, password hashing authentication,
error feedback, and session bootstrap.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable
import config
from backend.auth_service import AuthService

THEME = config.THEME
FONTS = config.FONTS

class LoginView(ttk.Frame):
    """Modern dark authentication screen."""

    def __init__(self, parent, on_login_success: Callable, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.on_login_success = on_login_success

        self.pack(fill="both", expand=True)

        # Center Container
        center_box = tk.Frame(self, bg=THEME["bg_card"], bd=1, relief="solid")
        center_box.place(relx=0.5, rely=0.5, anchor="center", width=420, height=480)

        # Header Badge / Icon
        top_accent = tk.Frame(center_box, bg=THEME["accent_primary"], height=6)
        top_accent.pack(side="top", fill="x")

        # Hospital Brand Header
        brand_frame = tk.Frame(center_box, bg=THEME["bg_card"], pady=20)
        brand_frame.pack(fill="x")

        tk.Label(
            brand_frame,
            text="+",
            bg=THEME["accent_primary"],
            fg="#ffffff",
            font=("Segoe UI", 22, "bold"),
            width=3,
            height=1
        ).pack(pady=(0, 10))

        tk.Label(
            brand_frame,
            text="HOSPITAL MANAGEMENT",
            bg=THEME["bg_card"],
            fg=THEME["text_primary"],
            font=("Segoe UI", 14, "bold")
        ).pack()

        tk.Label(
            brand_frame,
            text="Administrative Portal Login",
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"],
            font=FONTS["body"]
        ).pack(pady=(4, 0))

        # Form Container
        form_frame = tk.Frame(center_box, bg=THEME["bg_card"], padx=35)
        form_frame.pack(fill="both", expand=True)

        # Error notification label
        self.error_label = tk.Label(
            form_frame,
            text="",
            bg=THEME["bg_card"],
            fg=THEME["accent_danger"],
            font=FONTS["body_bold"],
            wraplength=340
        )
        self.error_label.pack(fill="x", pady=(0, 10))

        # Username Input
        tk.Label(form_frame, text="Username", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(anchor="w")
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(form_frame, textvariable=self.username_var, font=FONTS["body"])
        self.username_entry.pack(fill="x", pady=(4, 14), ipady=4)

        # Password Input
        tk.Label(form_frame, text="Password", bg=THEME["bg_card"], fg=THEME["text_secondary"], font=FONTS["body_bold"]).pack(anchor="w")
        self.password_var = tk.StringVar(value="admin123")
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", font=FONTS["body"])
        self.password_entry.pack(fill="x", pady=(4, 8), ipady=4)

        # Show password toggle
        self.show_pwd_var = tk.BooleanVar(value=False)
        self.show_pwd_cb = tk.Checkbutton(
            form_frame,
            text="Show password",
            variable=self.show_pwd_var,
            command=self._toggle_password_visibility,
            bg=THEME["bg_card"],
            fg=THEME["text_secondary"],
            activebackground=THEME["bg_card"],
            activeforeground=THEME["text_primary"],
            selectcolor=THEME["bg_dark"],
            font=FONTS["caption"]
        )
        self.show_pwd_cb.pack(anchor="w", pady=(0, 16))

        # Submit Button
        self.login_btn = ttk.Button(form_frame, text="Sign In to System", style="TButton", command=self._handle_login)
        self.login_btn.pack(fill="x", ipady=4)

        # Enter key triggers login
        self.username_entry.bind("<Return>", lambda e: self._handle_login())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())

        # Demo Credentials Hint
        hint_lbl = tk.Label(
            center_box,
            text="Default Credentials: admin / admin123",
            bg=THEME["bg_card"],
            fg=THEME["text_muted"],
            font=FONTS["caption"],
            pady=10
        )
        hint_lbl.pack(side="bottom")

    def _toggle_password_visibility(self):
        show_char = "" if self.show_pwd_var.get() else "*"
        self.password_entry.configure(show=show_char)

    def _handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        self.error_label.configure(text="")

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password.")
            return

        success, message, user = AuthService.login(username, password)
        if success:
            self.on_login_success(user)
        else:
            self.error_label.configure(text=message)
