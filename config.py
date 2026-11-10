"""
Configuration module for Intelligent Hospital Management and Analytics System.
Loads environment variables from .env with fallback defaults.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Manual .env parser fallback in case python-dotenv is not installed
def load_dotenv_fallback(env_path: Path):
    if not env_path.is_file():
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip("'\"")
            if k not in os.environ:
                os.environ[k] = v

env_file = BASE_DIR / '.env'
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file)
except ImportError:
    load_dotenv_fallback(env_file)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "hospital_management_system")

# Application Settings
APP_NAME = os.getenv("APP_NAME", "Intelligent Hospital Management and Analytics System")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# UI Styling Constants
THEME = {
    "bg_dark": "#0f172a",          # Slate 900
    "bg_card": "#1e293b",          # Slate 800
    "bg_card_hover": "#334155",    # Slate 700
    "bg_sidebar": "#0b1120",       # Deep Navy / Black Slate
    "sidebar_active": "#1e3a8a",   # Blue 900
    "accent_primary": "#2563eb",   # Royal Blue
    "accent_secondary": "#06b6d4", # Cyan
    "accent_success": "#10b981",   # Emerald green
    "accent_warning": "#f59e0b",   # Amber
    "accent_danger": "#ef4444",    # Crimson red
    "accent_critical": "#dc2626",  # Intense Red
    "text_primary": "#f8fafc",     # Slate 50
    "text_secondary": "#94a3b8",   # Slate 400
    "text_muted": "#64748b",       # Slate 500
    "border_color": "#334155",     # Slate 700
    "input_bg": "#0f172a",         # Slate 900
    "input_border": "#475569",     # Slate 600
}

FONTS = {
    "title": ("Segoe UI", 18, "bold"),
    "header": ("Segoe UI", 14, "bold"),
    "subheader": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "caption": ("Segoe UI", 9),
    "metric_number": ("Segoe UI", 24, "bold"),
}
