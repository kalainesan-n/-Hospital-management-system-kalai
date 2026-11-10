"""
UI Theme and Styles Configuration.
Provides a cohesive modern dark theme for Tkinter and ttk widgets.
"""

import tkinter as tk
from tkinter import ttk
import config

THEME = config.THEME
FONTS = config.FONTS

def apply_custom_theme(root: tk.Tk) -> ttk.Style:
    """Applies the dark aesthetic styling to all Tk and ttk widgets."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # General background configuration
    root.configure(bg=THEME["bg_dark"])

    # Configure TFrame
    style.configure("TFrame", background=THEME["bg_dark"])
    style.configure("Card.TFrame", background=THEME["bg_card"], relief="flat")
    style.configure("Sidebar.TFrame", background=THEME["bg_sidebar"])

    # Configure TLabel
    style.configure(
        "TLabel",
        background=THEME["bg_dark"],
        foreground=THEME["text_primary"],
        font=FONTS["body"]
    )
    style.configure(
        "Card.TLabel",
        background=THEME["bg_card"],
        foreground=THEME["text_primary"],
        font=FONTS["body"]
    )
    style.configure(
        "CardTitle.TLabel",
        background=THEME["bg_card"],
        foreground=THEME["text_secondary"],
        font=FONTS["caption"]
    )
    style.configure(
        "CardMetric.TLabel",
        background=THEME["bg_card"],
        foreground=THEME["text_primary"],
        font=FONTS["metric_number"]
    )
    style.configure(
        "HeaderTitle.TLabel",
        background=THEME["bg_dark"],
        foreground=THEME["text_primary"],
        font=FONTS["title"]
    )
    style.configure(
        "HeaderSubtitle.TLabel",
        background=THEME["bg_dark"],
        foreground=THEME["text_secondary"],
        font=FONTS["body"]
    )

    # Configure TButton
    style.configure(
        "TButton",
        background=THEME["accent_primary"],
        foreground="#ffffff",
        font=FONTS["body_bold"],
        borderwidth=0,
        focuscolor="none",
        padding=(12, 6)
    )
    style.map(
        "TButton",
        background=[("active", "#1d4ed8"), ("pressed", "#1e40af"), ("disabled", "#475569")],
        foreground=[("disabled", "#94a3b8")]
    )

    style.configure(
        "Success.TButton",
        background=THEME["accent_success"],
        foreground="#ffffff",
        font=FONTS["body_bold"],
        padding=(12, 6)
    )
    style.map("Success.TButton", background=[("active", "#059669")])

    style.configure(
        "Warning.TButton",
        background=THEME["accent_warning"],
        foreground="#000000",
        font=FONTS["body_bold"],
        padding=(12, 6)
    )
    style.map("Warning.TButton", background=[("active", "#d97706")])

    style.configure(
        "Danger.TButton",
        background=THEME["accent_danger"],
        foreground="#ffffff",
        font=FONTS["body_bold"],
        padding=(12, 6)
    )
    style.map("Danger.TButton", background=[("active", "#b91c1c")])

    style.configure(
        "Secondary.TButton",
        background=THEME["bg_card_hover"],
        foreground=THEME["text_primary"],
        font=FONTS["body"],
        padding=(10, 5)
    )
    style.map("Secondary.TButton", background=[("active", "#475569")])

    # Sidebar Navigation Buttons
    style.configure(
        "Nav.TButton",
        background=THEME["bg_sidebar"],
        foreground=THEME["text_secondary"],
        font=FONTS["body_bold"],
        anchor="w",
        padding=(16, 10),
        borderwidth=0
    )
    style.map(
        "Nav.TButton",
        background=[("active", THEME["bg_card"]), ("selected", THEME["sidebar_active"])],
        foreground=[("active", "#ffffff"), ("selected", "#ffffff")]
    )

    # Configure TEntry
    style.configure(
        "TEntry",
        fieldbackground=THEME["input_bg"],
        foreground=THEME["text_primary"],
        bordercolor=THEME["input_border"],
        lightcolor=THEME["input_border"],
        darkcolor=THEME["input_border"],
        padding=6
    )

    # Configure TCombobox
    style.configure(
        "TCombobox",
        fieldbackground=THEME["input_bg"],
        background=THEME["bg_card"],
        foreground=THEME["text_primary"],
        arrowcolor=THEME["text_primary"],
        padding=5
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", THEME["input_bg"])],
        foreground=[("readonly", THEME["text_primary"])]
    )

    # Configure Treeview (Data Tables)
    style.configure(
        "Treeview",
        background=THEME["bg_card"],
        foreground=THEME["text_primary"],
        fieldbackground=THEME["bg_card"],
        bordercolor=THEME["border_color"],
        rowheight=28,
        font=FONTS["body"]
    )
    style.map(
        "Treeview",
        background=[("selected", THEME["accent_primary"])],
        foreground=[("selected", "#ffffff")]
    )

    # Treeview Heading
    style.configure(
        "Treeview.Heading",
        background=THEME["bg_sidebar"],
        foreground=THEME["text_primary"],
        font=FONTS["body_bold"],
        relief="flat",
        padding=6
    )
    style.map(
        "Treeview.Heading",
        background=[("active", THEME["bg_card_hover"])],
        foreground=[("active", "#ffffff")]
    )

    # Configure TScrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=THEME["bg_card"],
        troughcolor=THEME["bg_dark"],
        bordercolor=THEME["border_color"],
        arrowcolor=THEME["text_secondary"]
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=THEME["bg_card"],
        troughcolor=THEME["bg_dark"],
        bordercolor=THEME["border_color"],
        arrowcolor=THEME["text_secondary"]
    )

    # Configure TNotebook
    style.configure("TNotebook", background=THEME["bg_dark"], borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background=THEME["bg_card"],
        foreground=THEME["text_secondary"],
        padding=(16, 8),
        font=FONTS["body_bold"]
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", THEME["accent_primary"])],
        foreground=[("selected", "#ffffff")]
    )

    return style
