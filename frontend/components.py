"""
Reusable UI Components for Desktop Interface.
Provides StatCard, HeaderBar, SearchBar, ModalDialog, StyledTreeview, and StatusBadge.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Optional, Callable
import config

THEME = config.THEME
FONTS = config.FONTS

class StatCard(ttk.Frame):
    """Modern KPI metric card with colored accent bar and bold typography."""

    def __init__(self, parent, title: str, value: str = "0", subtitle: str = "", accent_color: str = THEME["accent_primary"], **kwargs):
        super().__init__(parent, style="Card.TFrame", padding=0, **kwargs)
        self.accent_color = accent_color

        # Left color bar
        self.bar = tk.Frame(self, bg=accent_color, width=5)
        self.bar.pack(side="left", fill="y")

        # Content container
        content = ttk.Frame(self, style="Card.TFrame", padding=(16, 12))
        content.pack(side="left", fill="both", expand=True)

        self.title_lbl = ttk.Label(content, text=title.upper(), style="CardTitle.TLabel")
        self.title_lbl.pack(anchor="w")

        self.value_lbl = ttk.Label(content, text=str(value), style="CardMetric.TLabel")
        self.value_lbl.pack(anchor="w", pady=(2, 2))

        self.sub_lbl = ttk.Label(content, text=subtitle, style="CardTitle.TLabel")
        if subtitle:
            self.sub_lbl.pack(anchor="w")

    def update_value(self, value: Any, subtitle: Optional[str] = None):
        """Updates the numeric metric value displayed on the card."""
        self.value_lbl.configure(text=str(value))
        if subtitle is not None:
            self.sub_lbl.configure(text=subtitle)


class HeaderBar(ttk.Frame):
    """Top header panel with screen title, subtitle, and action buttons."""

    def __init__(self, parent, title: str, subtitle: str = "", on_refresh: Optional[Callable] = None, **kwargs):
        super().__init__(parent, style="TFrame", padding=(0, 0, 0, 16), **kwargs)

        left_box = ttk.Frame(self, style="TFrame")
        left_box.pack(side="left", fill="x", expand=True)

        self.title_lbl = ttk.Label(left_box, text=title, style="HeaderTitle.TLabel")
        self.title_lbl.pack(anchor="w")

        if subtitle:
            self.sub_lbl = ttk.Label(left_box, text=subtitle, style="HeaderSubtitle.TLabel")
            self.sub_lbl.pack(anchor="w", pady=(2, 0))

        if on_refresh:
            self.refresh_btn = ttk.Button(self, text="Refresh", style="Secondary.TButton", command=on_refresh)
            self.refresh_btn.pack(side="right", padx=(10, 0))


class SearchBar(ttk.Frame):
    """Integrated search input bar with search trigger and clear button."""

    def __init__(self, parent, placeholder: str = "Search...", on_search: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)
        self.on_search = on_search

        self.var = tk.StringVar()
        self.var.trace_add("write", lambda *args: self._on_text_change())

        self.entry = ttk.Entry(self, textvariable=self.var, width=35)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=3)

        self.search_btn = ttk.Button(self, text="Search", style="TButton", command=self._trigger_search)
        self.search_btn.pack(side="left", padx=(0, 4))

        self.clear_btn = ttk.Button(self, text="Clear", style="Secondary.TButton", command=self.clear)
        self.clear_btn.pack(side="left")

    def _trigger_search(self):
        if self.on_search:
            self.on_search(self.var.get().strip())

    def _on_text_change(self):
        # Trigger dynamic search if length is 0 (cleared)
        if len(self.var.get().strip()) == 0 and self.on_search:
            self.on_search("")

    def get(self) -> str:
        return self.var.get().strip()

    def clear(self):
        self.var.set("")
        if self.on_search:
            self.on_search("")


class StyledTreeview(ttk.Frame):
    """Data table wrapping ttk.Treeview with scrollbars, alternating rows, and column autosizing."""

    def __init__(self, parent, columns: List[str], headings: List[str], widths: Optional[List[int]] = None, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        self.columns = columns
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse", style="Treeview")

        for i, col in enumerate(columns):
            heading_text = headings[i] if i < len(headings) else col
            width = widths[i] if widths and i < len(widths) else 100
            self.tree.heading(col, text=heading_text, anchor="w")
            self.tree.column(col, width=width, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Alternating row tag colors
        self.tree.tag_configure("even", background=THEME["bg_card"])
        self.tree.tag_configure("odd", background="#172033")

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_rows(self, rows: List[List[Any]]):
        self.clear()
        for idx, row in enumerate(rows):
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert("", "end", values=row, tags=(tag,))

    def get_selected(self) -> Optional[List[Any]]:
        selected = self.tree.selection()
        if not selected:
            return None
        return self.tree.item(selected[0], "values")


class ModalDialog(tk.Toplevel):
    """Standardized popup modal dialog for forms and confirmation actions."""

    def __init__(self, parent, title: str, width: int = 500, height: int = 550):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.configure(bg=THEME["bg_dark"])
        self.transient(parent)
        self.grab_set()

        # Center on parent
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Top title bar inside window
        title_frame = tk.Frame(self, bg=THEME["bg_sidebar"], height=50)
        title_frame.pack(fill="x", side="top")
        tk.Label(
            title_frame,
            text=title,
            bg=THEME["bg_sidebar"],
            fg=THEME["text_primary"],
            font=FONTS["header"],
            padx=16,
            pady=12
        ).pack(anchor="w")

        # Scrollable form container
        self.canvas = tk.Canvas(self, bg=THEME["bg_dark"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.body_frame = ttk.Frame(self.canvas, style="TFrame", padding=16)

        self.body_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.body_frame, anchor="nw")
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="top", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y", before=self.canvas)

        # Error banner
        self.error_lbl = tk.Label(
            self.body_frame,
            text="",
            bg=THEME["bg_dark"],
            fg=THEME["accent_danger"],
            font=FONTS["body_bold"],
            wraplength=width - 50
        )
        self.error_lbl.pack(fill="x", pady=(0, 6))

        # Bottom action buttons
        self.button_frame = tk.Frame(self, bg=THEME["bg_sidebar"], height=60, padx=16, pady=12)
        self.button_frame.pack(fill="x", side="bottom")

    def show_error(self, message: str):
        self.error_lbl.configure(text=f"! {message}")

    def clear_error(self):
        self.error_lbl.configure(text="")
