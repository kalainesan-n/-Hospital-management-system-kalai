"""
Intelligent Hospital Management and Analytics System.
Application Entry Point.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Ensure root directory is on Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from frontend.theme import apply_custom_theme
from frontend.views.login_view import LoginView
from frontend.main_window import MainWindow
from database.connection import test_connection
from database.init_db import initialize_database

class HospitalApp:
    """Master application controller coordinating window lifecycle, theme, and authentication state."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry("1280x800")
        self.root.minsize(1100, 700)

        # Apply dark theme
        self.style = apply_custom_theme(self.root)

        # Center on screen
        self._center_window(1280, 800)

        # Force window to foreground
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)
        self.root.focus_force()

        # Master container
        self.container = ttk.Frame(self.root, style="TFrame")
        self.container.pack(fill="both", expand=True)

        self.current_screen = None

        # Verify database connectivity and seed if needed
        self.check_and_bootstrap_database()

        # Display Login screen initially
        self.show_login_screen()

        # Window closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _center_window(self, width: int, height: int):
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    def check_and_bootstrap_database(self):
        """Verifies MySQL connectivity. If accessible, auto-initializes database schema if missing."""
        connected, msg = test_connection()
        if not connected:
            # Let the user know via a clean banner or non-blocking prompt
            print(f"[Notice] MySQL check: {msg}")
            return

        try:
            # Check if database schema exists, else initialize
            initialize_database()
        except Exception as e:
            print(f"[Notice] Database auto-initialization message: {e}")

    def show_login_screen(self):
        """Renders the administrative authentication screen."""
        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = LoginView(self.container, on_login_success=self.show_main_window)

    def show_main_window(self, user: dict):
        """Renders the primary application shell with persistent navigation sidebar."""
        if self.current_screen:
            self.current_screen.destroy()

        self.current_screen = MainWindow(self.container, on_logout=self.show_login_screen, user=user)

    def on_close(self):
        """Gracefully terminates application."""
        self.root.destroy()


def main():
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
