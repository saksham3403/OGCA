"""Main Expense Tracker UI"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from config import COLORS, FONTS, WINDOW_WIDTH, WINDOW_HEIGHT, FEATURES
from utils import (
    CustomEntry, create_header, create_stat_card, format_currency,
    format_date, get_date_range, show_message, PremiumButton, Sidebar,
    validate_email
)
from database import Database
from pdf_generator import AccountingReportGenerator
from feature_manager import FeatureManager
from datetime import datetime, timedelta
import json
import shutil
import calendar
import smtplib, os, tempfile
import subprocess
import sys
import re
import logging
import io
import contextlib
from email.message import EmailMessage
from reportlab.pdfgen import canvas as pdf_canvas


class ExpenseTrackerUI:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data
        self.db = Database()
        self.user_id = user_data['id']
        self.current_page = "dashboard"
        self.feature_manager = FeatureManager(self.db, self.user_id)
        self.dashboard_account_scope = None
        self.insights_account_scope = "ALL"
        self.smtp_settings = {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": self.user_data.get("email", ""),
            "password": "",
            "use_tls": True,
        }
        self._tree_sort_orders = {}
        self._status_clear_job = None
        self.main_container = None
        self.right_section = None
        self.sidebar = None
        self.sidebar_width = 250
        self.sidebar_visible = True
        self._compact_mode = False
        self._quick_actions_visible = True
        self._last_layout_width = 0
        self.nav_toggle_btn = None
        self.quick_actions_frame = None
        self.quick_expense_btn = None
        self.quick_income_btn = None
        self.welcome_label = None
        self.global_nav_search_var = None
        self.sidebar_canvas = None
        self.sidebar_nav_frame = None
        self.sidebar_scrollbar = None
        self.sidebar_search_var = tk.StringVar()
        self.nav_button_map = {}
        self._active_nav_label = None
        self.page_subtitle_var = tk.StringVar(value="Overview and controls")
        self.clock_var = tk.StringVar(value="")
        self.theme_var = tk.StringVar(value="Ocean Blue")
        self.design_presets = {
            "Ocean Blue": {
                "primary": "#1e3a8a", "secondary": "#3b82f6", "accent": "#10b981",
                "danger": "#ef4444", "warning": "#f59e0b", "info": "#06b6d4",
                "success": "#059669", "background": "#f3f7ff", "surface": "#ffffff",
                "surface_alt": "#e9f0ff", "text_primary": "#111827", "text_secondary": "#475569",
                "border": "#dbe3f0", "border_dark": "#cbd5e1", "hover": "#dbeafe", "disabled": "#d1d5db"
            },
            "Midnight Graphite": {
                "primary": "#0f172a", "secondary": "#334155", "accent": "#22c55e",
                "danger": "#dc2626", "warning": "#d97706", "info": "#0ea5e9",
                "success": "#16a34a", "background": "#f8fafc", "surface": "#ffffff",
                "surface_alt": "#f1f5f9", "text_primary": "#0f172a", "text_secondary": "#475569",
                "border": "#cbd5e1", "border_dark": "#94a3b8", "hover": "#e2e8f0", "disabled": "#94a3b8"
            },
            "Emerald Finance": {
                "primary": "#065f46", "secondary": "#047857", "accent": "#0ea5e9",
                "danger": "#b91c1c", "warning": "#b45309", "info": "#0284c7",
                "success": "#059669", "background": "#f0fdf4", "surface": "#ffffff",
                "surface_alt": "#dcfce7", "text_primary": "#052e16", "text_secondary": "#166534",
                "border": "#bbf7d0", "border_dark": "#86efac", "hover": "#dcfce7", "disabled": "#86efac"
            },
            "Sunset Pro": {
                "primary": "#7c2d12", "secondary": "#ea580c", "accent": "#0284c7",
                "danger": "#b91c1c", "warning": "#ca8a04", "info": "#0e7490",
                "success": "#15803d", "background": "#fff7ed", "surface": "#ffffff",
                "surface_alt": "#ffedd5", "text_primary": "#431407", "text_secondary": "#9a3412",
                "border": "#fed7aa", "border_dark": "#fdba74", "hover": "#ffedd5", "disabled": "#fdba74"
            },
        }
        for key, value in self.design_presets[self.theme_var.get()].items():
            COLORS[key] = value
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Setup modern UI with sidebar"""
        self.parent.config(bg=COLORS["background"])
        self._configure_ttk_theme()
        
        # Main container
        main_container = tk.Frame(self.parent, bg=COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True)
        self.main_container = main_container
        
        # Sidebar
        self.sidebar = tk.Frame(main_container, bg=COLORS["primary"], width=self.sidebar_width)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        self.create_sidebar()
        
        # Right section (nav + content)
        right_section = tk.Frame(main_container, bg=COLORS["background"])
        right_section.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_section = right_section
        
        # Top navigation
        self.create_top_nav(right_section)
        
        # Main content area
        self.content_frame = tk.Frame(right_section, bg=COLORS["background"])
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Status bar for quick feedback
        status_bar = tk.Frame(right_section, bg=COLORS["surface"], height=28)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            status_bar,
            textvariable=self.status_var,
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"],
            anchor="w"
        ).pack(fill=tk.X, padx=12, pady=4)

        self._bind_shortcuts()
        self.parent.bind("<Configure>", self._on_root_resize)
        self.parent.after(120, self._sync_responsive_layout)
        
        # Show dashboard by default
        self.show_dashboard()

    def create_sidebar(self):
        """Create modern sidebar with navigation"""
        self.nav_buttons = []
        self.nav_button_map = {}
        self.page_label_by_key = {}
        # Branding
        branding = tk.Frame(self.sidebar, bg=COLORS["primary"])
        branding.pack(fill=tk.X, padx=15, pady=20)
        
        tk.Label(branding, text="OG CA", font=("Segoe UI", 14, "bold"),
                 fg="white", bg=COLORS["primary"]).pack(anchor=tk.W)
        tk.Label(branding, text="Control Account Suite", font=FONTS["small"],
                 fg=COLORS["secondary"], bg=COLORS["primary"]).pack(anchor=tk.W)
        
        # Separator
        tk.Frame(self.sidebar, bg=COLORS["secondary"], height=2).pack(fill=tk.X, padx=10, pady=10)

        search_wrap = tk.Frame(self.sidebar, bg=COLORS["primary"])
        search_wrap.pack(fill=tk.X, padx=10, pady=(0, 8))
        search_entry = ttk.Entry(search_wrap, textvariable=self.sidebar_search_var)
        search_entry.pack(fill=tk.X, ipady=4)
        search_entry.bind("<KeyRelease>", self._filter_sidebar_menu)

        nav_host = tk.Frame(self.sidebar, bg=COLORS["primary"])
        nav_host.pack(fill=tk.BOTH, expand=True, padx=6)

        self.sidebar_canvas = tk.Canvas(
            nav_host,
            bg=COLORS["primary"],
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT
        )
        self.sidebar_scrollbar = ttk.Scrollbar(nav_host, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_nav_frame = tk.Frame(self.sidebar_canvas, bg=COLORS["primary"])
        self.sidebar_nav_frame.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        )
        self.sidebar_canvas.create_window((0, 0), window=self.sidebar_nav_frame, anchor="nw")
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar_canvas.bind_all("<MouseWheel>", self._on_sidebar_mousewheel)
        
        # Navigation items
        nav_items = [
            ("Dashboard", "dashboard", self.show_dashboard),
            ("Transactions", "transactions", self.show_transactions),
            ("Accounts", "accounts", self.show_accounts),
            ("Reports", "reports", self.show_reports),
            ("Budget", "budget", self.show_budget),
            ("Goals", "goals", self.show_goals_center),
            ("Insights", "insights", self.show_insights_center),
            ("Notifications", "notifications", self.show_notification_center),
            ("Notes Hub", "notes", self.show_notes_hub),
            ("Reminders", "reminders", self.show_reminders_hub),
            ("Data Quality", "data_quality", self.show_data_quality_center),
            ("Scenario Lab", "scenario", self.show_scenario_lab),
            ("User Manager", "user_manager", self.open_user_manager_app),
            ("Profile", "profile", self.show_profile),
            ("Features", "features", self.show_features),
        ]
        
        for label, page_key, command in nav_items:
            self.create_nav_button(label, page_key, command)
        
        # Separator
        tk.Frame(self.sidebar, bg=COLORS["secondary"], height=2).pack(fill=tk.X, padx=10, pady=10, side=tk.BOTTOM)
        
        # Footer with logout
        footer = tk.Frame(self.sidebar, bg=COLORS["primary"])
        footer.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        
        logout_btn = tk.Button(footer, text="Logout", bg=COLORS["danger"], fg="white",
                               font=FONTS["body"], relief=tk.FLAT, cursor="hand2",
                               command=self.logout, width=20)
        logout_btn.pack(pady=5)

    def create_nav_button(self, label, page_key, command):
        """Create sidebar navigation button"""
        btn = tk.Button(self.sidebar_nav_frame, text=label, command=command,
                       bg=COLORS["primary"], fg="white", font=FONTS["body"],
                       relief=tk.FLAT, anchor="w", padx=20, pady=12, cursor="hand2")
        btn.pack(fill=tk.X, pady=2)
        btn.bind("<Enter>", lambda e, l=label: self._handle_nav_hover(l, True))
        btn.bind("<Leave>", lambda e, l=label: self._handle_nav_hover(l, False))
        self.nav_buttons.append(btn)
        self.nav_button_map[label] = btn
        self.page_label_by_key[page_key] = label

    def _handle_nav_hover(self, label, entering):
        """Hover state that respects active module highlighting."""
        btn = self.nav_button_map.get(label)
        if not btn:
            return
        if label == self._active_nav_label:
            btn.config(bg=COLORS["secondary"])
            return
        btn.config(bg=COLORS["secondary"] if entering else COLORS["primary"])

    def _set_active_nav(self, page_key):
        """Highlight current active page in sidebar."""
        active_label = self.page_label_by_key.get(page_key)
        self._active_nav_label = active_label
        for label, btn in self.nav_button_map.items():
            if label == active_label:
                btn.config(bg=COLORS["secondary"], fg="white")
            else:
                btn.config(bg=COLORS["primary"], fg="white")

    def _on_sidebar_mousewheel(self, event):
        """Enable mousewheel scrolling for sidebar nav."""
        if self.sidebar_canvas and self.sidebar_canvas.winfo_exists():
            self.sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _filter_sidebar_menu(self, event=None):
        """Filter sidebar menu items by typed query."""
        query = self.sidebar_search_var.get().strip().lower()
        for btn in self.nav_buttons:
            label = str(btn.cget("text")).lower()
            if not query or query in label:
                btn.pack(fill=tk.X, pady=2)
            else:
                btn.pack_forget()
        self._set_active_nav(self.current_page)


    def create_top_nav(self, parent):
        """Create modern top navigation bar"""
        nav_frame = tk.Frame(parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        nav_frame.pack(fill=tk.X, padx=0, pady=0)

        # Left side - page title
        left = tk.Frame(nav_frame, bg=COLORS["surface"])
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20, pady=15)

        self.nav_toggle_btn = tk.Button(
            left, text="Hide Menu", command=self.toggle_sidebar,
            font=FONTS["small"], bg=COLORS["surface_alt"], fg=COLORS["text_primary"],
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        )
        self.nav_toggle_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.page_title = tk.Label(left, text="Dashboard", font=FONTS["heading"],
                                   fg=COLORS["text_primary"], bg=COLORS["surface"])
        self.page_title.pack(side=tk.LEFT, anchor=tk.W)
        self.page_subtitle = tk.Label(
            left,
            textvariable=self.page_subtitle_var,
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"]
        )
        self.page_subtitle.pack(side=tk.LEFT, padx=(12, 0))

        # Right side - quick actions + user info
        right = tk.Frame(nav_frame, bg=COLORS["surface"])
        right.pack(side=tk.RIGHT, padx=20, pady=15)

        self.global_nav_search_var = tk.StringVar()
        search_entry = ttk.Entry(right, textvariable=self.global_nav_search_var, width=22)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        search_entry.bind("<Return>", self._handle_global_nav_search)

        self.theme_combo = ttk.Combobox(
            right,
            textvariable=self.theme_var,
            values=list(self.design_presets.keys()),
            width=16,
            state="readonly",
        )
        self.theme_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        tk.Button(
            right, text="Command", command=self.open_command_palette,
            font=FONTS["small"], bg=COLORS["surface_alt"], fg=COLORS["text_primary"],
            relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))

        quick_actions = tk.Frame(right, bg=COLORS["surface"])
        quick_actions.pack(side=tk.LEFT, padx=(0, 12))
        self.quick_actions_frame = quick_actions

        self.quick_expense_btn = tk.Button(quick_actions, text="+ Expense", command=self.quick_add_expense, font=FONTS["small"], bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.quick_expense_btn.pack(side=tk.LEFT, padx=4)
        self.quick_income_btn = tk.Button(quick_actions, text="+ Income", command=self.quick_add_income, font=FONTS["small"], bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=10, pady=5, cursor="hand2")
        self.quick_income_btn.pack(side=tk.LEFT, padx=4)

        user_name = self.user_data.get("username") or self.user_data.get("full_name", "User")
        self.welcome_label = tk.Label(right, text=f"Welcome {user_name}", font=FONTS["body"], fg=COLORS["text_secondary"], bg=COLORS["surface"])
        self.welcome_label.pack(side=tk.LEFT)
        self.clock_label = tk.Label(right, textvariable=self.clock_var, font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"])
        self.clock_label.pack(side=tk.LEFT, padx=(10, 0))
        self._start_clock()

    def _start_clock(self):
        """Live clock in top navigation."""
        if not self.parent.winfo_exists():
            return
        self.clock_var.set(datetime.now().strftime("%a %d %b %Y | %H:%M:%S"))
        self.parent.after(1000, self._start_clock)

    def _set_view_state(self, page_key, title, subtitle, status_message):
        """Centralized state updates for consistent UX."""
        self.current_page = page_key
        self.page_title.config(text=title)
        self.page_subtitle_var.set(subtitle)
        self._set_active_nav(page_key)
        self.set_status(status_message, auto_clear=True)

    def toggle_sidebar(self):
        """Manually toggle sidebar visibility."""
        if self._compact_mode:
            self._set_sidebar_visible(not self.sidebar_visible)
            return
        self._set_sidebar_visible(not self.sidebar_visible)

    def _set_sidebar_visible(self, visible):
        """Show/hide sidebar safely."""
        if visible == self.sidebar_visible:
            return

        self.sidebar_visible = visible
        if visible:
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y, before=self.right_section)
        else:
            self.sidebar.pack_forget()

    def _set_compact_mode(self, enabled):
        """Apply compact nav layout on smaller window widths."""
        if enabled == self._compact_mode:
            return

        self._compact_mode = enabled
        user_name = self.user_data.get("username") or self.user_data.get("full_name", "User")

        if enabled:
            self._set_sidebar_visible(False)
            if self.quick_actions_frame and self._quick_actions_visible:
                self.quick_actions_frame.pack_forget()
                self._quick_actions_visible = False
            if self.welcome_label:
                self.welcome_label.config(text=user_name)
            if self.nav_toggle_btn:
                self.nav_toggle_btn.config(text="Menu")
        else:
            self._set_sidebar_visible(True)
            if self.quick_actions_frame and not self._quick_actions_visible:
                self.quick_actions_frame.pack(side=tk.LEFT, padx=(0, 12))
                self._quick_actions_visible = True
            if self.welcome_label:
                self.welcome_label.config(text=f"Welcome {user_name}")
            if self.nav_toggle_btn:
                self.nav_toggle_btn.config(text="Hide Menu")

    def _sync_responsive_layout(self):
        width = self.parent.winfo_width()
        if width <= 1:
            return
        self._set_compact_mode(width < 1180)

    def _on_root_resize(self, event=None):
        """Window resize observer for responsive behavior."""
        width = self.parent.winfo_width()
        if abs(width - self._last_layout_width) < 20:
            return
        self._last_layout_width = width
        self._sync_responsive_layout()

    def _handle_global_nav_search(self, event=None):
        """Navigate quickly to a module from the top search box."""
        raw = (self.global_nav_search_var.get() if self.global_nav_search_var else "").strip().lower()
        if not raw:
            return
        actions = {
            "dashboard": self.show_dashboard,
            "transactions": self.show_transactions,
            "accounts": self.show_accounts,
            "reports": self.show_reports,
            "budget": self.show_budget,
            "goals": self.show_goals_center,
            "insights": self.show_insights_center,
            "notifications": self.show_notification_center,
            "notes": self.show_notes_hub,
            "reminders": self.show_reminders_hub,
            "data quality": self.show_data_quality_center,
            "scenario": self.show_scenario_lab,
            "profile": self.show_profile,
            "features": self.show_features,
            "user manager": self.open_user_manager_app,
            "users": self.open_user_manager_app,
        }

        for key, action in actions.items():
            if raw in key:
                action()
                self.set_status(f"Opened: {key.title()}", auto_clear=True)
                self.global_nav_search_var.set("")
                return

        self.set_status("No matching module found", auto_clear=True)

    def _configure_ttk_theme(self):
        """Apply a cleaner ttk theme for notebook/table widgets."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", font=FONTS["body"], padding=(14, 8), background=COLORS["surface"], foreground=COLORS["text_secondary"])
        style.map("TNotebook.Tab", background=[("selected", COLORS["primary"])], foreground=[("selected", "white")])
        style.configure("Treeview", rowheight=28, font=FONTS["small"], background=COLORS["surface"], foreground=COLORS["text_primary"], fieldbackground=COLORS["surface"], borderwidth=0)
        style.configure("Treeview.Heading", font=FONTS["body"], background=COLORS["primary"], foreground="white", relief=tk.FLAT)
        style.map("Treeview", background=[("selected", COLORS["secondary"])], foreground=[("selected", "white")])

    def open_user_manager_app(self):
        """Launch standalone user manager application."""
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_manager.py")
        if not os.path.exists(script_path):
            show_message(self.parent, "Error", "user_manager.py not found", "error")
            return
        try:
            subprocess.Popen([sys.executable, script_path])
            self.set_status("User Manager launched", auto_clear=True)
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to launch User Manager: {e}", "error")

    def _on_theme_change(self, event=None):
        """Apply selected design preset live."""
        self.apply_design_preset(self.theme_var.get())

    def apply_design_preset(self, preset_name):
        """Update app palette from preset and refresh active page."""
        preset = self.design_presets.get(preset_name)
        if not preset:
            return
        for key, value in preset.items():
            COLORS[key] = value

        try:
            self.parent.configure(bg=COLORS["background"])
            if self.main_container:
                self.main_container.configure(bg=COLORS["background"])
            if self.sidebar:
                self.sidebar.configure(bg=COLORS["primary"])
            if self.right_section:
                self.right_section.configure(bg=COLORS["background"])
            self._configure_ttk_theme()
            self.refresh_current_page()
            self.set_status(f"Theme changed: {preset_name}", auto_clear=True)
        except Exception:
            pass

    def open_command_palette(self):
        """Power command palette for quick feature access."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Command Palette")
        dlg.geometry("620x420")
        dlg.configure(bg=COLORS["background"])
        dlg.transient(self.parent)
        dlg.grab_set()

        tk.Label(dlg, text="Command Palette", font=FONTS["heading"], bg=COLORS["background"], fg=COLORS["text_primary"]).pack(anchor=tk.W, padx=16, pady=(14, 6))
        query_var = tk.StringVar()
        entry = ttk.Entry(dlg, textvariable=query_var)
        entry.pack(fill=tk.X, padx=16, pady=(0, 10), ipady=6)

        commands = [
            ("Open Dashboard", self.show_dashboard),
            ("Open Transactions", self.show_transactions),
            ("Open Accounts", self.show_accounts),
            ("Open Reports", self.show_reports),
            ("Open Budget", self.show_budget),
            ("Open Goals Planner", self.show_goals_center),
            ("Open Insights Center", self.show_insights_center),
            ("Open Notifications", self.show_notification_center),
            ("Open Notes Hub", self.show_notes_hub),
            ("Open Reminders", self.show_reminders_hub),
            ("Open Data Quality", self.show_data_quality_center),
            ("Open Scenario Lab", self.show_scenario_lab),
            ("Generate Smart Alerts", lambda: self.db.generate_system_notifications(self.user_id)),
            ("Launch User Manager", self.open_user_manager_app),
        ]

        listbox = tk.Listbox(dlg, font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"], relief=tk.FLAT, selectbackground=COLORS["secondary"], selectforeground="white")
        listbox.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        def render():
            listbox.delete(0, tk.END)
            q = query_var.get().strip().lower()
            for name, _ in commands:
                if not q or q in name.lower():
                    listbox.insert(tk.END, name)
            if listbox.size() > 0:
                listbox.selection_set(0)

        def run_selected(event=None):
            if not listbox.curselection():
                return
            choice = listbox.get(listbox.curselection()[0])
            for name, action in commands:
                if name == choice:
                    action()
                    dlg.destroy()
                    self.set_status(f"Executed: {name}", auto_clear=True)
                    return

        entry.bind("<KeyRelease>", lambda e: render())
        entry.bind("<Return>", run_selected)
        listbox.bind("<Double-Button-1>", run_selected)
        listbox.bind("<Return>", run_selected)
        render()
        entry.focus_set()

    def set_status(self, message, auto_clear=False):
        """Update status text with a timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"{message}  |  {timestamp}")

        if self._status_clear_job:
            self.parent.after_cancel(self._status_clear_job)
            self._status_clear_job = None

        if auto_clear:
            self._status_clear_job = self.parent.after(5000, lambda: self.status_var.set("Ready"))

    def _bind_shortcuts(self):
        """Keyboard shortcuts for common actions."""
        self.parent.bind("<Control-Key-1>", lambda e: self.show_dashboard())
        self.parent.bind("<Control-Key-2>", lambda e: self.show_transactions())
        self.parent.bind("<Control-Key-3>", lambda e: self.show_reports())
        self.parent.bind("<Control-Key-4>", lambda e: self.show_accounts())
        self.parent.bind("<Control-Key-5>", lambda e: self.show_goals_center())
        self.parent.bind("<Control-Key-6>", lambda e: self.show_insights_center())
        self.parent.bind("<Control-Key-7>", lambda e: self.show_notification_center())
        self.parent.bind("<Control-Key-8>", lambda e: self.show_notes_hub())
        self.parent.bind("<Control-Key-9>", lambda e: self.show_reminders_hub())
        self.parent.bind("<Control-k>", lambda e: self.open_command_palette())
        self.parent.bind("<Control-K>", lambda e: self.open_command_palette())
        self.parent.bind("<Control-n>", lambda e: self.quick_add_expense())
        self.parent.bind("<Control-N>", lambda e: self.quick_add_income())
        self.parent.bind("<F5>", lambda e: self.refresh_current_page())

    def refresh_current_page(self):
        """Refresh active view quickly."""
        refresh_map = {
            "dashboard": self.show_dashboard,
            "transactions": self.show_transactions,
            "accounts": self.show_accounts,
            "reports": self.show_reports,
            "budget": self.show_budget,
            "goals": self.show_goals_center,
            "insights": self.show_insights_center,
            "notifications": self.show_notification_center,
            "notes": self.show_notes_hub,
            "reminders": self.show_reminders_hub,
            "data_quality": self.show_data_quality_center,
            "scenario": self.show_scenario_lab,
            "profile": self.show_profile,
            "features": self.show_features,
        }
        refresh_action = refresh_map.get(self.current_page, self.show_dashboard)
        refresh_action()
        self.set_status("View refreshed", auto_clear=True)

    def quick_add_expense(self):
        """Fast add flow for expenses from any page."""
        category = simpledialog.askstring("Quick Expense", "Category:", parent=self.parent)
        if category is None:
            return
        amount_str = simpledialog.askstring("Quick Expense", "Amount:", parent=self.parent)
        if amount_str is None:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            show_message(self.parent, "Error", "Invalid amount", "error")
            return

        self.db.add_expense(self.user_id, category.strip() or "Other", amount, str(datetime.now().date()), "Quick add", "Other")
        self.load_data()
        self.set_status(f"Expense added: {category} ({format_currency(amount)})", auto_clear=True)
        if self.current_page in ("dashboard", "transactions"):
            self.refresh_current_page()

    def quick_add_income(self):
        """Fast add flow for income from any page."""
        source = simpledialog.askstring("Quick Income", "Source:", parent=self.parent)
        if source is None:
            return
        amount_str = simpledialog.askstring("Quick Income", "Amount:", parent=self.parent)
        if amount_str is None:
            return
        try:
            amount = float(amount_str)
        except ValueError:
            show_message(self.parent, "Error", "Invalid amount", "error")
            return

        self.db.add_income(self.user_id, source.strip() or "Other", amount, str(datetime.now().date()), "Quick add")
        self.load_data()
        self.set_status(f"Income added: {source} ({format_currency(amount)})", auto_clear=True)
        if self.current_page in ("dashboard", "transactions"):
            self.refresh_current_page()

    @staticmethod
    def _row_matches_search(row_values, query):
        """Case-insensitive row matching for table filters."""
        joined = " ".join(str(value or "") for value in row_values).lower()
        return query in joined

    def _attach_tree_sorting(self, tree, columns):
        """Enable click-to-sort for table columns."""
        for col in columns:
            tree.heading(col, text=col, command=lambda c=col: self._sort_tree_by_column(tree, c))

    def _sort_tree_by_column(self, tree, column):
        """Sort tree rows by selected column."""
        order_key = (id(tree), column)
        descending = self._tree_sort_orders.get(order_key, False)
        rows = [(tree.set(item, column), item) for item in tree.get_children("")]

        def normalize(value):
            text = str(value).replace(",", "").strip()
            try:
                return float(text)
            except ValueError:
                return text.lower()

        rows.sort(key=lambda x: normalize(x[0]), reverse=descending)
        for index, (_, item) in enumerate(rows):
            tree.move(item, "", index)

        self._tree_sort_orders[order_key] = not descending
        direction = "descending" if descending else "ascending"
        self.set_status(f"Sorted by {column} ({direction})", auto_clear=True)

    def _smart_suggest_category(self, description):
        """Suggest category using keyword rules + history."""
        text = (description or "").strip().lower()
        if not text:
            return None

        keyword_map = {
            "Food": ["food", "restaurant", "cafe", "zomato", "swiggy", "dinner", "lunch"],
            "Transport": ["uber", "ola", "taxi", "metro", "bus", "fuel", "petrol", "diesel"],
            "Utilities": ["electricity", "water", "internet", "wifi", "gas", "bill", "recharge"],
            "Entertainment": ["movie", "netflix", "spotify", "game", "concert"],
            "Healthcare": ["doctor", "medicine", "pharmacy", "hospital", "clinic"],
            "Education": ["course", "tuition", "book", "exam", "school", "college"],
        }
        for category, words in keyword_map.items():
            if any(word in text for word in words):
                return category

        return self.db.suggest_category(self.user_id, text)

    def _open_date_picker(self, target_entry, initial_date=None):
        """Open a lightweight calendar picker and write selected date to target CustomEntry."""
        try:
            base = datetime.strptime(initial_date or target_entry.get(), "%Y-%m-%d")
        except Exception:
            base = datetime.now()

        picker = tk.Toplevel(self.parent)
        picker.title("Select Date")
        picker.geometry("320x320")
        picker.config(bg=COLORS["background"])
        picker.transient(self.parent)
        picker.grab_set()

        month_var = tk.IntVar(value=base.month)
        year_var = tk.IntVar(value=base.year)

        header = tk.Frame(picker, bg=COLORS["background"])
        header.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(header, text="<", command=lambda: move_month(-1), bg=COLORS["secondary"], fg="white", relief=tk.FLAT, width=3).pack(side=tk.LEFT)
        title_var = tk.StringVar()
        tk.Label(header, textvariable=title_var, bg=COLORS["background"], fg=COLORS["text_primary"], font=FONTS["subheading"]).pack(side=tk.LEFT, expand=True)
        tk.Button(header, text=">", command=lambda: move_month(1), bg=COLORS["secondary"], fg="white", relief=tk.FLAT, width=3).pack(side=tk.RIGHT)

        grid = tk.Frame(picker, bg=COLORS["background"])
        grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, wd in enumerate(weekdays):
            tk.Label(grid, text=wd, bg=COLORS["background"], fg=COLORS["text_secondary"], font=FONTS["small"]).grid(row=0, column=i, padx=4, pady=4)

        def select_day(day):
            selected = datetime(year_var.get(), month_var.get(), day).strftime("%Y-%m-%d")
            target_entry.set(selected)
            picker.destroy()

        def render_days():
            # clear old day buttons
            for child in grid.winfo_children():
                info = child.grid_info()
                if int(info.get("row", 0)) > 0:
                    child.destroy()

            year = year_var.get()
            month = month_var.get()
            title_var.set(f"{calendar.month_name[month]} {year}")
            weeks = calendar.monthcalendar(year, month)
            for r, week in enumerate(weeks, start=1):
                for c, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid, text="", bg=COLORS["background"]).grid(row=r, column=c, padx=2, pady=2)
                    else:
                        btn = tk.Button(
                            grid,
                            text=str(day),
                            command=lambda d=day: select_day(d),
                            bg=COLORS["surface"],
                            fg=COLORS["text_primary"],
                            relief=tk.FLAT,
                            width=3,
                            cursor="hand2"
                        )
                        btn.grid(row=r, column=c, padx=2, pady=2)

        def move_month(delta):
            m = month_var.get() + delta
            y = year_var.get()
            if m < 1:
                m = 12
                y -= 1
            elif m > 12:
                m = 1
                y += 1
            month_var.set(m)
            year_var.set(y)
            render_days()

        render_days()

    def _extract_receipt_text(self, image_path):
        """OCR text extraction using pytesseract if available."""
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(image_path))
        except Exception:
            return ""

    def _parse_receipt_data(self, text):
        """Extract probable amount/date/category from OCR text."""
        clean = (text or "").lower()
        amount = None
        date_text = None
        category = None

        amounts = re.findall(r'(\d+[.,]\d{2})', clean)
        if amounts:
            try:
                amount = max(float(a.replace(",", ".")) for a in amounts)
            except Exception:
                amount = None

        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', clean) or re.search(r'(\d{2}/\d{2}/\d{4})', clean)
        if date_match:
            date_text = date_match.group(1).replace("/", "-")

        category = self._smart_suggest_category(clean) or "Other"
        return {"amount": amount, "date": date_text, "category": category}

    @staticmethod
    def _normalize_statement_date(raw_date):
        """Convert statement date formats into YYYY-MM-DD."""
        raw = (raw_date or "").strip()
        formats = ["%b %d, %Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw

    @staticmethod
    def _phonepe_transaction_regex():
        return re.compile(
            r'^(?P<date>[A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+'
            r'(?P<details>.+?)\s+'
            r'(?P<type>DEBIT|CREDIT)\s+'
            r'(?P<amount>[^\s]+)$'
        )

    def _parse_phonepe_statement_pdf(self, pdf_path):
        """Parse multi-page PhonePe-style statement and return transactions list."""
        try:
            import pdfplumber
        except Exception:
            raise RuntimeError("pdfplumber is required for PDF import. Install with: pip install pdfplumber")
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        logging.getLogger("pdfplumber").setLevel(logging.ERROR)

        pattern = self._phonepe_transaction_regex()
        transactions = []
        with contextlib.redirect_stderr(io.StringIO()):
            with pdfplumber.open(pdf_path) as pdf:
                for page_no, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
                    current = None

                    for line in lines:
                        if line.startswith("Page ") or "system generated statement" in line.lower():
                            continue
                        if line.startswith("Date Transaction Details") or line.startswith("Transaction Statement for"):
                            continue
                        if re.match(r'^\d{2}\D\d{2}\s*(am|pm)$', line.lower()):
                            # orphan time line in odd extraction, ignore
                            continue

                        m = pattern.match(line)
                        if m:
                            if current:
                                transactions.append(current)
                            raw_date = m.group("date")
                            details = m.group("details").strip()
                            txn_type = m.group("type").upper()
                            raw_amount = m.group("amount")
                            cleaned_amount = re.sub(r'[^0-9.,]', '', raw_amount).replace(",", "")
                            amount = float(cleaned_amount) if cleaned_amount else 0.0
                            current = {
                                "date": self._normalize_statement_date(raw_date),
                                "raw_date": raw_date,
                                "details": details,
                                "type": txn_type,
                                "amount": amount,
                                "txn_id": "",
                                "utr_no": "",
                                "page": page_no,
                            }
                            continue

                        if current:
                            txn_id_match = re.search(r'Transaction ID\s+([A-Za-z0-9]+)', line, flags=re.IGNORECASE)
                            if txn_id_match:
                                current["txn_id"] = txn_id_match.group(1)
                            utr_match = re.search(r'UTR No\.\s*([A-Za-z0-9]+)', line, flags=re.IGNORECASE)
                            if utr_match:
                                current["utr_no"] = utr_match.group(1)

                    if current:
                        transactions.append(current)

        # de-duplicate by txn_id (or fallback tuple)
        seen = set()
        deduped = []
        for t in transactions:
            key = t["txn_id"] or f"{t['date']}|{t['type']}|{t['amount']}|{t['details']}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(t)
        return deduped

    def _smart_enhance_statement_description(self, details, txn_type, txn_id, provider="Statement"):
        """Create cleaner description from raw statement details."""
        d = (details or "").strip()
        if d.lower().startswith("paid to "):
            base = d[8:].strip()
            desc = f"{provider} payment to {base}"
        elif d.lower().startswith("received from "):
            base = d[14:].strip()
            desc = f"{provider} receipt from {base}"
        else:
            desc = f"{provider} {txn_type.lower()} - {d}"
        if txn_id:
            desc = f"{desc} ({txn_id})"
        return desc[:160]

    def _detect_statement_provider(self, sample_text):
        """Best-effort provider detection from PDF text."""
        s = (sample_text or "").lower()
        if "phonepe" in s:
            return "PhonePe"
        if "paytm" in s:
            return "Paytm"
        if "google pay" in s or "gpay" in s:
            return "GPay"
        return "Generic"

    def _parse_generic_upi_statement_pdf(self, pdf_path):
        """Generic parser for UPI/payment statement formats."""
        try:
            import pdfplumber
        except Exception:
            raise RuntimeError("pdfplumber is required for PDF import. Install with: pip install pdfplumber")
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        logging.getLogger("pdfplumber").setLevel(logging.ERROR)

        pattern = re.compile(
            r'^(?P<date>[A-Za-z]{3}\s+\d{1,2},\s+\d{4}|\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})\s+'
            r'(?P<details>.+?)\s+'
            r'(?:(?P<type>DEBIT|CREDIT)\s+)?'
            r'(?P<amount>[^\s]+)$',
            flags=re.IGNORECASE
        )

        txns = []
        with contextlib.redirect_stderr(io.StringIO()):
            with pdfplumber.open(pdf_path) as pdf:
                for page_no, page in enumerate(pdf.pages, start=1):
                    lines = [ln.strip() for ln in (page.extract_text() or "").splitlines() if ln.strip()]
                    current = None
                    for line in lines:
                        low = line.lower()
                        if line.startswith("Page ") or "system generated statement" in low or line.startswith("Date Transaction"):
                            continue
                        m = pattern.match(line)
                        if m:
                            if current:
                                txns.append(current)
                            raw_date = m.group("date")
                            details = m.group("details").strip()
                            raw_amount = m.group("amount")
                            cleaned_amount = re.sub(r'[^0-9.,]', '', raw_amount).replace(",", "")
                            amount = float(cleaned_amount) if cleaned_amount else 0.0
                            txn_type = (m.group("type") or "").upper()
                            if not txn_type:
                                dl = details.lower()
                                if "paid to" in dl or "sent to" in dl or "debit" in dl:
                                    txn_type = "DEBIT"
                                elif "received" in dl or "credit" in dl:
                                    txn_type = "CREDIT"
                                else:
                                    txn_type = "DEBIT"
                            current = {
                                "date": self._normalize_statement_date(raw_date),
                                "raw_date": raw_date,
                                "details": details,
                                "type": txn_type,
                                "amount": amount,
                                "txn_id": "",
                                "utr_no": "",
                                "page": page_no,
                            }
                            continue
                        if current:
                            txn_id_match = re.search(r'(?:Transaction ID|Txn ID)\s*[:.]?\s*([A-Za-z0-9]+)', line, flags=re.IGNORECASE)
                            if txn_id_match:
                                current["txn_id"] = txn_id_match.group(1)
                            utr_match = re.search(r'UTR(?: No\.)?\s*[:.]?\s*([A-Za-z0-9]+)', line, flags=re.IGNORECASE)
                            if utr_match:
                                current["utr_no"] = utr_match.group(1)
                    if current:
                        txns.append(current)

        seen = set()
        out = []
        for t in txns:
            key = t["txn_id"] or f"{t['date']}|{t['type']}|{t['amount']}|{t['details']}"
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
        return out

    def _parse_statement_pdf(self, pdf_path, preset="Auto"):
        """Parse PDF statement using selected preset."""
        try:
            import pdfplumber
            with contextlib.redirect_stderr(io.StringIO()):
                with pdfplumber.open(pdf_path) as pdf:
                    first_text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
        except Exception:
            first_text = ""

        provider = self._detect_statement_provider(first_text) if preset == "Auto" else preset
        provider = provider or "Generic"

        if provider == "PhonePe":
            txns = self._parse_phonepe_statement_pdf(pdf_path)
        else:
            txns = self._parse_generic_upi_statement_pdf(pdf_path)
        return provider, txns

    def manage_import_rules(self, on_change=None):
        """Manage merchant keyword import rules."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Statement Import Rules")
        dlg.geometry("900x460")
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)
        dlg.grab_set()

        top = tk.Frame(dlg, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        top.pack(fill=tk.X, padx=12, pady=12)
        keyword_entry = CustomEntry(top, placeholder="Keyword (e.g., medical, goibibo)")
        keyword_entry.grid(row=0, column=1, padx=6, pady=8, sticky=tk.W)
        category_entry = CustomEntry(top, placeholder="Category")
        category_entry.grid(row=0, column=3, padx=6, pady=8, sticky=tk.W)

        accounts = self.db.get_managed_accounts(self.user_id)
        account_options = ["", "Personal (Main)"] + [a["account_name"] for a in accounts]
        account_var = tk.StringVar(value="")
        ttk.Combobox(top, textvariable=account_var, values=account_options, width=20).grid(row=0, column=5, padx=6, pady=8, sticky=tk.W)

        tk.Label(top, text="Keyword", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=0, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Category", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=2, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Account", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=4, padx=6, pady=8, sticky=tk.W)

        frame = tk.Frame(dlg, bg=COLORS["background"])
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        cols = ("ID", "Keyword", "Category", "Account")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != "Keyword" else 300)
        self._attach_tree_sorting(tree, cols)
        tree.pack(fill=tk.BOTH, expand=True)

        def refresh():
            tree.delete(*tree.get_children())
            for r in self.db.get_import_rules(self.user_id):
                tree.insert("", "end", values=(r["id"], r["keyword"], r["category"], r.get("account_name", "")))
            if on_change:
                on_change()

        def add_rule():
            kw = keyword_entry.get().strip().lower()
            cat = category_entry.get().strip()
            acc = account_var.get().strip()
            if not kw or not cat:
                show_message(self.parent, "Error", "Keyword and category are required", "error")
                return
            self.db.add_import_rule(self.user_id, kw, cat, acc)
            keyword_entry.clear()
            category_entry.clear()
            account_var.set("")
            refresh()

        def delete_rule():
            sel = tree.selection()
            if not sel:
                return
            rid = int(tree.item(sel[0], "values")[0])
            self.db.delete_import_rule(rid, self.user_id)
            refresh()

        btns = tk.Frame(dlg, bg=COLORS["background"])
        btns.pack(fill=tk.X, padx=12, pady=(0, 12))
        tk.Button(btns, text="Add Rule", command=add_rule, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Delete Selected", command=delete_rule, bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Close", command=dlg.destroy, bg=COLORS["text_secondary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.RIGHT, padx=4)
        refresh()

    def import_statement_pdf(self):
        """Import transactions from PDF statement with account selection and smart category sync."""
        pdf_path = filedialog.askopenfilename(
            title="Select Statement PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not pdf_path:
            return

        preset = simpledialog.askstring(
            "Statement Preset",
            "Choose parser preset: Auto / PhonePe / Paytm / GPay / Generic",
            initialvalue="Auto"
        )
        if preset is None:
            return
        preset = preset.strip()
        if preset not in {"Auto", "PhonePe", "Paytm", "GPay", "Generic"}:
            preset = "Auto"

        try:
            provider, parsed = self._parse_statement_pdf(pdf_path, preset=preset)
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to parse PDF: {e}", "error")
            return

        if not parsed:
            show_message(self.parent, "Info", "No transactions found in this PDF", "info")
            return

        # account selection
        accounts = self.db.get_managed_accounts(self.user_id)
        account_map = {"Personal (Main)": None}
        account_options = ["Personal (Main)"]
        for acc in accounts:
            account_options.append(acc["account_name"])
            account_map[acc["account_name"]] = acc["id"]

        dlg = tk.Toplevel(self.parent)
        dlg.title("Import Statement Preview")
        dlg.geometry("1200x760")
        dlg.minsize(1000, 640)
        dlg.resizable(True, True)
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        header.pack(fill=tk.X, padx=12, pady=12)
        tk.Label(header, text=f"File: {os.path.basename(pdf_path)}", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(anchor=tk.W, padx=10, pady=(8, 4))
        tk.Label(header, text=f"Provider: {provider} | Detected transactions: {len(parsed)}", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["small"]).pack(anchor=tk.W, padx=10, pady=(0, 8))

        controls = tk.Frame(dlg, bg=COLORS["background"])
        controls.pack(fill=tk.X, padx=12, pady=(0, 8))
        tk.Label(controls, text="Import into account:", bg=COLORS["background"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(side=tk.LEFT, padx=(0, 8))
        account_var = tk.StringVar(value="Personal (Main)")
        ttk.Combobox(controls, textvariable=account_var, values=account_options, width=28).pack(side=tk.LEFT)
        # Keep a top save button visible regardless of tree height/scale.
        top_save_btn = tk.Button(
            controls,
            text="Save Transactions",
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=14,
            pady=7
        )
        top_save_btn.pack(side=tk.RIGHT, padx=6)

        tree_frame = tk.Frame(dlg, bg=COLORS["background"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        cols = ("Date", "Type", "Amount", "Category", "Description", "Txn ID")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=18)
        widths = {"Date": 95, "Type": 80, "Amount": 90, "Category": 110, "Description": 500, "Txn ID": 180}
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 120))
        self._attach_tree_sorting(tree, cols)
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        preview_rows = []
        for idx, txn in enumerate(parsed):
            rule = self.db.find_import_rule(self.user_id, txn["details"])
            category = (rule["category"] if rule else None) or self._smart_suggest_category(txn["details"]) or ("Income" if txn["type"] == "CREDIT" else "Other")
            desc = self._smart_enhance_statement_description(txn["details"], txn["type"], txn["txn_id"], provider=provider)
            row = {**txn, "category": category, "description": desc, "rule_account_name": (rule.get("account_name") if rule else "")}
            preview_rows.append(row)
            tree.insert("", "end", iid=str(idx), values=(txn["date"], txn["type"], f"{txn['amount']:.2f}", category, desc, txn["txn_id"]))

        def refresh_preview():
            tree.delete(*tree.get_children())
            for i, row in enumerate(preview_rows):
                tree.insert("", "end", iid=str(i), values=(row["date"], row["type"], f"{float(row['amount']):.2f}", row["category"], row["description"], row.get("txn_id", "")))

        def edit_selected():
            sel = tree.selection()
            if not sel:
                return
            idx = int(sel[0])
            row = preview_rows[idx]
            ed = tk.Toplevel(dlg)
            ed.title("Edit Row")
            ed.geometry("560x320")
            ed.config(bg=COLORS["background"])
            ed.transient(dlg)
            ed.grab_set()

            body = tk.Frame(ed, bg=COLORS["background"])
            body.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
            date_e = CustomEntry(body); date_e.set(str(row.get("date",""))); date_e.pack(fill=tk.X, pady=6)
            type_var = tk.StringVar(value=row.get("type","DEBIT"))
            ttk.Combobox(body, textvariable=type_var, values=["DEBIT","CREDIT"], width=10).pack(fill=tk.X, pady=6)
            amt_e = CustomEntry(body); amt_e.set(str(row.get("amount",""))); amt_e.pack(fill=tk.X, pady=6)
            cat_e = CustomEntry(body); cat_e.set(str(row.get("category","Other"))); cat_e.pack(fill=tk.X, pady=6)
            desc_e = CustomEntry(body); desc_e.set(str(row.get("description",""))); desc_e.pack(fill=tk.X, pady=6)

            def save_row():
                try:
                    amount = float(amt_e.get())
                except ValueError:
                    show_message(ed, "Error", "Invalid amount", "error")
                    return
                row["date"] = date_e.get().strip()
                row["type"] = type_var.get().strip().upper() or "DEBIT"
                row["amount"] = amount
                row["category"] = cat_e.get().strip() or "Other"
                row["description"] = desc_e.get().strip() or row["details"]
                refresh_preview()
                ed.destroy()

            tk.Button(body, text="Save", command=save_row, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.RIGHT, padx=4, pady=8)
            tk.Button(body, text="Cancel", command=ed.destroy, bg=COLORS["text_secondary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.RIGHT, padx=4, pady=8)

        tree.bind("<Double-1>", lambda e: edit_selected())

        summary_var = tk.StringVar(value="")
        tk.Label(dlg, textvariable=summary_var, bg=COLORS["background"], fg=COLORS["text_secondary"], font=FONTS["small"]).pack(side=tk.BOTTOM, anchor=tk.W, padx=14, pady=(0, 8))

        def reapply_rules():
            for row in preview_rows:
                rule = self.db.find_import_rule(self.user_id, row["details"])
                if rule:
                    row["category"] = rule["category"]
                    row["rule_account_name"] = rule.get("account_name", "")
                elif not row.get("category"):
                    row["category"] = self._smart_suggest_category(row["details"]) or ("Income" if row["type"] == "CREDIT" else "Other")
            refresh_preview()

        def do_import():
            account_id = account_map.get(account_var.get())
            imported = 0
            skipped = 0
            for row in preview_rows:
                txn_id = row.get("txn_id", "")
                if txn_id and self.db.statement_txn_exists(self.user_id, txn_id):
                    skipped += 1
                    continue

                mapped_account = row.get("rule_account_name", "")
                row_account_id = account_map.get(mapped_account, account_id) if mapped_account else account_id

                notes = f"[STATEMENT:{txn_id}] [UTR:{row.get('utr_no','')}] [SOURCE:{provider} PDF]".strip()
                if row["type"] == "DEBIT":
                    self.db.add_expense(
                        self.user_id,
                        row["category"],
                        float(row["amount"]),
                        row["date"],
                        row["description"],
                        "UPI",
                        notes=notes,
                        account_id=row_account_id,
                    )
                    imported += 1
                elif row["type"] == "CREDIT":
                    self.db.add_income(
                        self.user_id,
                        row["description"],
                        float(row["amount"]),
                        row["date"],
                        f"Imported from statement {txn_id}",
                        notes=notes,
                        account_id=row_account_id,
                    )
                    imported += 1
                else:
                    skipped += 1

            self.load_data()
            self.set_status(f"Statement import done. Imported={imported}, skipped={skipped}", auto_clear=True)
            summary_var.set(f"Imported: {imported} | Skipped duplicates/unknown: {skipped}")
            show_message(self.parent, "Success", f"Statement imported.\nImported: {imported}\nSkipped: {skipped}", "info")
            self.refresh_current_page()
            dlg.destroy()

        footer = tk.Frame(dlg, bg=COLORS["background"])
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(4, 12))

        left_actions = tk.Frame(footer, bg=COLORS["background"])
        left_actions.pack(side=tk.LEFT)
        tk.Button(left_actions, text="Manage Rules", bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=8, command=lambda: self.manage_import_rules(on_change=reapply_rules)).pack(side=tk.LEFT, padx=6)
        tk.Button(left_actions, text="Apply Rules", bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=8, command=reapply_rules).pack(side=tk.LEFT, padx=6)
        tk.Button(left_actions, text="Edit Selected", bg=COLORS["warning"], fg="white", relief=tk.FLAT, padx=12, pady=8, command=edit_selected).pack(side=tk.LEFT, padx=6)

        right_actions = tk.Frame(footer, bg=COLORS["background"])
        right_actions.pack(side=tk.RIGHT)
        tk.Button(right_actions, text="Cancel", bg=COLORS["text_secondary"], fg="white", relief=tk.FLAT, padx=14, pady=8, command=dlg.destroy).pack(side=tk.RIGHT, padx=6)
        tk.Button(right_actions, text="Save Transactions", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=16, pady=8, command=do_import).pack(side=tk.RIGHT, padx=6)

        # Keep backward-compatible label too.
        tk.Button(
            right_actions,
            text="Import",
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=12,
            pady=8,
            command=do_import
        ).pack(side=tk.RIGHT, padx=6)
        top_save_btn.config(command=do_import)

        total = sum(r["amount"] for r in preview_rows)
        debit_total = sum(r["amount"] for r in preview_rows if r["type"] == "DEBIT")
        credit_total = sum(r["amount"] for r in preview_rows if r["type"] == "CREDIT")
        summary_var.set(
            f"Preview totals -> Count: {len(preview_rows)} | Debit: {debit_total:.2f} | Credit: {credit_total:.2f} | Total Movement: {total:.2f}"
        )

    def open_trash_bin(self):
        """Open recoverable trash bin dialog."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Trash Bin")
        dlg.geometry("900x420")
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)

        frame = tk.Frame(dlg, bg=COLORS["background"])
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        cols = ("Trash ID", "Type", "Deleted At", "Summary")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140 if col != "Summary" else 430)
        self._attach_tree_sorting(tree, cols)
        tree.pack(fill=tk.BOTH, expand=True)

        def refresh():
            tree.delete(*tree.get_children())
            for item in self.db.get_trash_items(self.user_id):
                data = item.get("item_data", {})
                if item["item_type"] == "expense":
                    summary = f"{data.get('category','')} | {data.get('amount','')} | {data.get('date','')}"
                else:
                    summary = f"{data.get('source','')} | {data.get('amount','')} | {data.get('date','')}"
                tree.insert("", "end", values=(item["id"], item["item_type"], item["deleted_at"], summary))

        btns = tk.Frame(dlg, bg=COLORS["background"])
        btns.pack(fill=tk.X, padx=12, pady=(0, 12))

        def restore_selected():
            selected = tree.selection()
            if not selected:
                return
            trash_id = int(tree.item(selected[0], "values")[0])
            ok, msg = self.db.restore_trash_item(trash_id, self.user_id)
            if ok:
                self.set_status("Item restored from trash", auto_clear=True)
                refresh()
            else:
                show_message(self.parent, "Error", f"Restore failed: {msg}", "error")

        def delete_selected():
            selected = tree.selection()
            if not selected:
                return
            trash_id = int(tree.item(selected[0], "values")[0])
            if self.db.delete_trash_item(trash_id, self.user_id):
                refresh()

        tk.Button(btns, text="Restore Selected", bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=restore_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Delete Permanently", bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=delete_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Refresh", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=refresh).pack(side=tk.LEFT, padx=4)
        refresh()

    def configure_report_designer(self):
        """Customize report branding/layout settings."""
        current = self.db.get_report_design(self.user_id) or {}
        brand_name = simpledialog.askstring("Report Designer", "Brand Name:", initialvalue=current.get("brand_name", "OG CA"))
        if brand_name is None:
            return
        primary_color = simpledialog.askstring("Report Designer", "Primary Color Hex (#1e3a8a):", initialvalue=current.get("primary_color", "#1e3a8a"))
        if primary_color is None:
            return
        footer_note = simpledialog.askstring("Report Designer", "Footer Note:", initialvalue=current.get("footer_note", "Generated by OG CA"))
        if footer_note is None:
            return
        layout_mode = simpledialog.askstring("Report Designer", "Layout Mode (standard/compact):", initialvalue=current.get("layout_mode", "standard"))
        if layout_mode is None:
            return

        self.db.set_report_design(self.user_id, brand_name.strip(), primary_color.strip(), footer_note.strip(), layout_mode.strip().lower())
        self.set_status("Report design settings saved", auto_clear=True)
        show_message(self.parent, "Success", "Report designer settings updated", "info")

    def open_subscription_center(self):
        """Manage subscriptions with renewal alerts."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("Subscription Center")
        dlg.geometry("980x520")
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)

        top = tk.Frame(dlg, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        top.pack(fill=tk.X, padx=12, pady=12)

        name_entry = CustomEntry(top, placeholder="Subscription Name")
        amount_entry = CustomEntry(top, placeholder="Amount")
        cycle_var = tk.StringVar(value="Monthly")
        date_entry = CustomEntry(top, placeholder="YYYY-MM-DD")
        date_entry.set(str(datetime.now().date()))
        category_var = tk.StringVar(value="Utilities")

        tk.Label(top, text="Name", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=0, padx=6, pady=8, sticky=tk.W)
        name_entry.grid(row=0, column=1, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Amount", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=2, padx=6, pady=8, sticky=tk.W)
        amount_entry.grid(row=0, column=3, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Cycle", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=4, padx=6, pady=8, sticky=tk.W)
        ttk.Combobox(top, textvariable=cycle_var, values=["Weekly", "Monthly", "Quarterly", "Yearly"], width=12).grid(row=0, column=5, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Next Billing", bg=COLORS["surface"], font=FONTS["body"]).grid(row=1, column=0, padx=6, pady=8, sticky=tk.W)
        date_entry.grid(row=1, column=1, padx=6, pady=8, sticky=tk.W)
        tk.Label(top, text="Category", bg=COLORS["surface"], font=FONTS["body"]).grid(row=1, column=2, padx=6, pady=8, sticky=tk.W)
        ttk.Combobox(top, textvariable=category_var, values=["Utilities", "Entertainment", "Education", "Other"], width=14).grid(row=1, column=3, padx=6, pady=8, sticky=tk.W)

        table_frame = tk.Frame(dlg, bg=COLORS["background"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        cols = ("ID", "Name", "Amount", "Cycle", "Next Billing", "Status", "Days Left")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120 if col != "Name" else 220)
        self._attach_tree_sorting(tree, cols)
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_subs():
            tree.delete(*tree.get_children())
            today = datetime.now().date()
            for s in self.db.get_subscriptions(self.user_id):
                try:
                    d = datetime.strptime(s["next_billing_date"], "%Y-%m-%d").date()
                    days_left = (d - today).days
                except Exception:
                    days_left = ""
                tree.insert("", "end", values=(s["id"], s["name"], f"{float(s['amount']):.2f}", s["billing_cycle"], s["next_billing_date"], s["status"], days_left))

        def add_sub():
            try:
                amt = float(amount_entry.get())
            except ValueError:
                show_message(self.parent, "Error", "Invalid amount", "error")
                return
            try:
                datetime.strptime(date_entry.get().strip(), "%Y-%m-%d")
            except ValueError:
                show_message(self.parent, "Error", "Date must be YYYY-MM-DD", "error")
                return
            self.db.add_subscription(
                self.user_id,
                name_entry.get().strip() or "Subscription",
                amt,
                cycle_var.get().strip(),
                date_entry.get().strip(),
                category_var.get().strip(),
                "",
            )
            refresh_subs()

        def toggle_status():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            new_status = "paused" if vals[5] == "active" else "active"
            self.db.update_subscription(int(vals[0]), self.user_id, status=new_status)
            refresh_subs()

        def delete_sub():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            self.db.delete_subscription(int(vals[0]), self.user_id)
            refresh_subs()

        btns = tk.Frame(dlg, bg=COLORS["background"])
        btns.pack(fill=tk.X, padx=12, pady=(0, 12))
        tk.Button(btns, text="Add Subscription", command=add_sub, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Pause/Resume", command=toggle_status, bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Delete", command=delete_sub, bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Refresh", command=refresh_subs, bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        refresh_subs()

    def generate_invoice_pdf(self):
        """Generate client invoice PDF."""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Invoice Generator")
        dialog.geometry("760x560")
        dialog.config(bg=COLORS["background"])
        dialog.transient(self.parent)

        frame = tk.Frame(dialog, bg=COLORS["background"])
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        client_entry = CustomEntry(frame, placeholder="Client Name")
        email_entry = CustomEntry(frame, placeholder="Client Email")
        invoice_no_entry = CustomEntry(frame, placeholder="Invoice Number")
        due_entry = CustomEntry(frame, placeholder="Due Date (YYYY-MM-DD)")
        due_entry.set(str((datetime.now() + timedelta(days=14)).date()))
        items_txt = tk.Text(frame, height=14, font=FONTS["small"])
        items_txt.insert("1.0", "Description,Qty,Rate\nConsulting,1,5000")

        tk.Label(frame, text="Client Name", bg=COLORS["background"], font=FONTS["body"]).pack(anchor=tk.W)
        client_entry.pack(fill=tk.X, pady=4)
        tk.Label(frame, text="Client Email", bg=COLORS["background"], font=FONTS["body"]).pack(anchor=tk.W)
        email_entry.pack(fill=tk.X, pady=4)
        tk.Label(frame, text="Invoice Number", bg=COLORS["background"], font=FONTS["body"]).pack(anchor=tk.W)
        invoice_no_entry.pack(fill=tk.X, pady=4)
        tk.Label(frame, text="Due Date", bg=COLORS["background"], font=FONTS["body"]).pack(anchor=tk.W)
        due_entry.pack(fill=tk.X, pady=4)
        tk.Label(frame, text="Items (one per line: Description,Qty,Rate)", bg=COLORS["background"], font=FONTS["body"]).pack(anchor=tk.W, pady=(8, 4))
        items_txt.pack(fill=tk.BOTH, expand=True)

        def export_invoice():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"Invoice_{invoice_no_entry.get().strip() or datetime.now().strftime('%Y%m%d')}.pdf",
            )
            if not file_path:
                return
            design = self.db.get_report_design(self.user_id) or {}
            brand_name = design.get("brand_name") or "OG CA"
            footer_note = design.get("footer_note") or "Generated by OG CA"
            color = design.get("primary_color") or "#1e3a8a"

            try:
                c = pdf_canvas.Canvas(file_path, pagesize=(595, 842))
                c.setFillColor(color)
                c.rect(0, 800, 595, 42, fill=1)
                c.setFillColor("white")
                c.setFont("Helvetica-Bold", 16)
                c.drawString(30, 815, f"{brand_name} - Invoice")

                c.setFillColor("black")
                c.setFont("Helvetica", 11)
                c.drawString(30, 770, f"Invoice #: {invoice_no_entry.get().strip() or 'N/A'}")
                c.drawString(30, 752, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}")
                c.drawString(30, 734, f"Due Date: {due_entry.get().strip()}")
                c.drawString(30, 710, f"Bill To: {client_entry.get().strip()}")
                c.drawString(30, 692, f"Email: {email_entry.get().strip()}")

                y = 650
                c.setFont("Helvetica-Bold", 11)
                c.drawString(30, y, "Description")
                c.drawString(320, y, "Qty")
                c.drawString(390, y, "Rate")
                c.drawString(470, y, "Amount")
                c.line(30, y - 4, 560, y - 4)
                y -= 24

                total = 0.0
                lines = [ln.strip() for ln in items_txt.get("1.0", tk.END).splitlines() if ln.strip()]
                if lines and "description,qty,rate" in lines[0].lower():
                    lines = lines[1:]
                for ln in lines:
                    parts = [p.strip() for p in ln.split(",")]
                    if len(parts) < 3:
                        continue
                    desc = parts[0]
                    qty = float(parts[1])
                    rate = float(parts[2])
                    amount = qty * rate
                    total += amount
                    c.setFont("Helvetica", 10)
                    c.drawString(30, y, desc[:45])
                    c.drawString(320, y, f"{qty:g}")
                    c.drawString(390, y, f"{rate:.2f}")
                    c.drawString(470, y, f"{amount:.2f}")
                    y -= 18
                    if y < 120:
                        c.showPage()
                        y = 780

                c.line(360, y - 8, 560, y - 8)
                c.setFont("Helvetica-Bold", 12)
                c.drawString(390, y - 26, "Total:")
                c.drawString(470, y - 26, f"{total:.2f}")
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(30, 40, footer_note)
                c.save()
                self.set_status("Invoice generated", auto_clear=True)
                show_message(self.parent, "Success", f"Invoice saved to {file_path}", "info")
            except Exception as e:
                show_message(self.parent, "Error", f"Failed to generate invoice: {e}", "error")

        tk.Button(frame, text="Export Invoice PDF", command=export_invoice, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=14, pady=8).pack(anchor=tk.E, pady=(8, 0))

    def clear_content(self):
        """Clear content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def load_data(self):
        """Load data from database"""
        self.summary = self.db.get_summary(self.user_id)
        self.category_summary = self.db.get_category_summary(self.user_id)

    def _filter_rows_by_account_scope(self, rows, scope):
        """Filter expense/income rows by dashboard account scope."""
        if scope == "ALL":
            return rows
        if scope is None:
            return [r for r in rows if r.get("account_id") in (None, "", 0)]
        return [r for r in rows if r.get("account_id") == scope]

    def show_dashboard(self):
        """Show enhanced dashboard"""
        self._set_view_state("dashboard", "Dashboard", "Financial pulse and quick actions", "Dashboard loaded")
        self.clear_content()
        self.load_data()

        # Scope selector: show calculations for selected account only
        accounts = self.db.get_managed_accounts(self.user_id)
        scope_map = {"All Accounts": "ALL", "Personal (Main)": None}
        for acc in accounts:
            scope_map[acc["account_name"]] = acc["id"]

        # Default to first managed account (firm) if available, else personal
        if self.dashboard_account_scope not in scope_map.values():
            self.dashboard_account_scope = accounts[0]["id"] if accounts else None

        scope_label_map = {v: k for k, v in scope_map.items()}
        selected_scope_label = scope_label_map.get(self.dashboard_account_scope, "Personal (Main)")

        scope_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        scope_frame.pack(fill=tk.X, padx=20, pady=(8, 0))
        tk.Label(
            scope_frame,
            text="Dashboard Scope:",
            font=FONTS["body"],
            fg=COLORS["text_primary"],
            bg=COLORS["background"]
        ).pack(side=tk.LEFT, padx=(0, 8))

        scope_var = tk.StringVar(value=selected_scope_label)
        scope_combo = ttk.Combobox(scope_frame, textvariable=scope_var, values=list(scope_map.keys()), width=26, state="readonly")
        scope_combo.pack(side=tk.LEFT)

        def apply_scope_change(event=None):
            self.dashboard_account_scope = scope_map.get(scope_var.get(), None)
            self.show_dashboard()

        scope_combo.bind("<<ComboboxSelected>>", apply_scope_change)

        all_expenses_full = self.db.get_expenses(self.user_id)
        all_income_full = self.db.get_income(self.user_id)
        all_expenses = self._filter_rows_by_account_scope(all_expenses_full, self.dashboard_account_scope)
        all_income = self._filter_rows_by_account_scope(all_income_full, self.dashboard_account_scope)

        local_summary = {
            "total_income": sum(float(i.get("amount", 0)) for i in all_income),
            "total_expenses": sum(float(e.get("amount", 0)) for e in all_expenses),
        }
        local_summary["balance"] = local_summary["total_income"] - local_summary["total_expenses"]

        cat_totals = {}
        for exp in all_expenses:
            cat = exp.get("category", "Other")
            if cat not in cat_totals:
                cat_totals[cat] = {"category": cat, "total": 0.0, "count": 0}
            cat_totals[cat]["total"] += float(exp.get("amount", 0))
            cat_totals[cat]["count"] += 1
        local_category_summary = sorted(cat_totals.values(), key=lambda x: x["total"], reverse=True)

        # Main stats container with 4 cards
        stats_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Calculate additional metrics
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # This month's spending
        this_month_expenses = sum(
            e['amount'] for e in all_expenses 
            if datetime.strptime(e['date'], '%Y-%m-%d').month == current_month 
            and datetime.strptime(e['date'], '%Y-%m-%d').year == current_year
        )
        
        # Average daily spending
        days_passed = max(1, datetime.now().day)
        daily_average = this_month_expenses / days_passed if this_month_expenses > 0 else 0
        
        create_stat_card(stats_frame, "Total Balance", format_currency(local_summary['balance']), COLORS["primary"])
        create_stat_card(stats_frame, "Total Income", format_currency(local_summary['total_income']), COLORS["accent"])
        create_stat_card(stats_frame, "Total Expenses", format_currency(local_summary['total_expenses']), COLORS["danger"])
        create_stat_card(stats_frame, "Daily Average", format_currency(daily_average), COLORS["warning"])

        workspace_strip = tk.Frame(self.content_frame, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        workspace_strip.pack(fill=tk.X, padx=20, pady=(2, 8))
        tk.Label(
            workspace_strip,
            text="Workspace Quick Launch",
            font=FONTS["subheading"],
            fg=COLORS["primary"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, padx=12, pady=10)

        quick_launch = [
            ("Goals", self.show_goals_center, COLORS["primary"]),
            ("Insights", self.show_insights_center, COLORS["secondary"]),
            ("Notes", self.show_notes_hub, COLORS["accent"]),
            ("Reminders", self.show_reminders_hub, COLORS["warning"]),
            ("Quality", self.show_data_quality_center, COLORS["info"]),
            ("Scenario", self.show_scenario_lab, COLORS["danger"]),
        ]
        for label, action, color in quick_launch:
            tk.Button(
                workspace_strip,
                text=label,
                command=action,
                font=FONTS["small"],
                bg=color,
                fg="white",
                relief=tk.FLAT,
                padx=9,
                pady=5,
                cursor="hand2",
            ).pack(side=tk.RIGHT, padx=4)
        
        # Content section - two column layout
        content = tk.Frame(self.content_frame, bg=COLORS["background"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left side - Recent transactions with enhanced styling
        left_frame = tk.Frame(content, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Header with action button
        header_frame = tk.Frame(left_frame, bg=COLORS["surface"])
        header_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(
            header_frame,
            text="Recent Transactions",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, anchor=tk.W, expand=True)
        
        view_all_btn = tk.Button(
            header_frame,
            text="View All ->",
            font=FONTS["small"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.show_transactions
        )
        view_all_btn.pack(side=tk.RIGHT)
        view_all_btn.bind("<Enter>", lambda e: view_all_btn.config(bg=COLORS["secondary"]))
        view_all_btn.bind("<Leave>", lambda e: view_all_btn.config(bg=COLORS["primary"]))
        
        # Recent transactions list with better formatting
        expenses = all_expenses[:8]
        if expenses:
            for i, expense in enumerate(expenses):
                trans_frame = tk.Frame(left_frame, bg=COLORS["background"] if i % 2 == 0 else COLORS["surface"])
                trans_frame.pack(fill=tk.X, padx=0)
                
                inner_frame = tk.Frame(trans_frame, bg=trans_frame.cget("bg"))
                inner_frame.pack(fill=tk.X, padx=15, pady=8)
                
                # Category label with icon
                tk.Label(
                    inner_frame,
                    text=f"- {expense['category']}",
                    font=FONTS["body"],
                    fg=COLORS["text_primary"],
                    bg=trans_frame.cget("bg")
                ).pack(side=tk.LEFT, anchor=tk.W)
                
                # Date
                tk.Label(
                    inner_frame,
                    text=expense['date'],
                    font=FONTS["small"],
                    fg=COLORS["text_secondary"],
                    bg=trans_frame.cget("bg")
                ).pack(side=tk.RIGHT, padx=(20, 0))
                
                # Amount
                tk.Label(
                    inner_frame,
                    text=f"-Rs. {expense['amount']:.2f}",
                    font=(FONTS["body"][0], FONTS["body"][1], "bold"),
                    fg=COLORS["danger"],
                    bg=trans_frame.cget("bg")
                ).pack(side=tk.RIGHT, padx=(10, 0))
        else:
            tk.Label(
                left_frame,
                text="No transactions yet - Start by adding an expense",
                font=FONTS["body"],
                fg=COLORS["text_secondary"],
                bg=COLORS["surface"]
            ).pack(pady=30)
        
        # Right side - Enhanced category breakdown with better visualization
        right_frame = tk.Frame(content, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Header
        cat_header = tk.Frame(right_frame, bg=COLORS["surface"])
        cat_header.pack(fill=tk.X, padx=15, pady=(15, 10))
        
        tk.Label(
            cat_header,
            text="Expenses by Category",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, anchor=tk.W, expand=True)
        
        cat_chart_btn = tk.Button(
            cat_header,
            text="View Chart ->",
            font=FONTS["small"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.show_category_chart
        )
        cat_chart_btn.pack(side=tk.RIGHT)
        cat_chart_btn.bind("<Enter>", lambda e: cat_chart_btn.config(bg=COLORS["secondary"]))
        cat_chart_btn.bind("<Leave>", lambda e: cat_chart_btn.config(bg=COLORS["primary"]))
        
        if local_category_summary:
            total_expenses = local_summary['total_expenses']
            for item in local_category_summary[:6]:
                percentage = (item['total'] / total_expenses * 100) if total_expenses > 0 else 0
                
                cat_frame = tk.Frame(right_frame, bg=COLORS["background"])
                cat_frame.pack(fill=tk.X, padx=15, pady=6)
                
                # Category name and percentage
                info_frame = tk.Frame(cat_frame, bg=COLORS["background"])
                info_frame.pack(fill=tk.X)
                
                tk.Label(
                    info_frame,
                    text=item['category'],
                    font=FONTS["body"],
                    fg=COLORS["text_primary"],
                    bg=COLORS["background"],
                    width=18,
                    anchor=tk.W
                ).pack(side=tk.LEFT)
                
                tk.Label(
                    info_frame,
                    text=f"Rs. {item['total']:.2f}",
                    font=FONTS["small"],
                    fg=COLORS["text_secondary"],
                    bg=COLORS["background"]
                ).pack(side=tk.RIGHT, padx=(5, 0))
                
                # Progress bar with color coding
                bar_frame = tk.Frame(cat_frame, bg=COLORS["border"], height=8, relief=tk.FLAT)
                bar_frame.pack(fill=tk.X, pady=(5, 0))
                
                # Color based on percentage
                if percentage > 50:
                    bar_color = COLORS["danger"]
                elif percentage > 30:
                    bar_color = COLORS["warning"]
                else:
                    bar_color = COLORS["accent"]
                
                filled_width = int(percentage)
                if filled_width > 0:
                    filled_frame = tk.Frame(bar_frame, bg=bar_color, height=8)
                    filled_frame.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=0)
                    filled_frame.config(width=int(filled_width * 2.4))
                
                # Percentage text
                tk.Label(
                    cat_frame,
                    text=f"{percentage:.1f}%",
                    font=FONTS["small"],
                    fg=COLORS["text_secondary"],
                    bg=COLORS["background"]
                ).pack(anchor=tk.E, padx=0, pady=(2, 0))
        else:
            tk.Label(
                right_frame,
                text="No expenses yet - Add some transactions",
                font=FONTS["body"],
                fg=COLORS["text_secondary"],
                bg=COLORS["surface"]
            ).pack(pady=30)
        
        # Bottom section - Enhanced insights with analytics
        insights_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        insights_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(
            insights_frame,
            text="Analytics & Insights",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["background"]
        ).pack(anchor=tk.W, pady=(10, 5))
        
        insights_box = tk.Frame(insights_frame, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        insights_box.pack(fill=tk.X)
        
        # Get real analytics from feature manager
        # Localized analytics for selected scope
        savings_rate = (local_summary["balance"] / local_summary["total_income"] * 100) if local_summary["total_income"] > 0 else 0
        expense_ratio = (local_summary["total_expenses"] / local_summary["total_income"] * 100) if local_summary["total_income"] > 0 else 100 if local_summary["total_expenses"] > 0 else 0
        health_score = max(0, min(100, int(100 - expense_ratio + (10 if local_summary["balance"] > 0 else 0))))
        smart_insights = []
        if local_category_summary:
            smart_insights.append(f"Highest spend category: {local_category_summary[0]['category']}")
        if savings_rate < 0:
            smart_insights.append("Negative savings in this scope. Review high-value spends.")
        elif savings_rate < 10:
            smart_insights.append("Low savings rate. Consider reducing discretionary expenses.")
        budget_alerts = self.feature_manager.get_budget_alerts()
        
        health_color = COLORS["accent"] if health_score > 70 else (COLORS["warning"] if health_score > 40 else COLORS["danger"])
        
        insights_content = tk.Frame(insights_box, bg=COLORS["surface"])
        insights_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Basic stats
        tk.Label(insights_content, text=f"This month's spending: Rs. {this_month_expenses:.2f}", 
                font=FONTS["body"], fg=COLORS["text_primary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=3)
        tk.Label(insights_content, text=f"Daily average: Rs. {daily_average:.2f}", 
                font=FONTS["body"], fg=COLORS["text_primary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=3)
        
        # Top category
        if local_category_summary:
            tk.Label(insights_content, text=f"Top category: {local_category_summary[0]['category']} (Rs. {local_category_summary[0]['total']:.2f})", 
                    font=FONTS["body"], fg=COLORS["text_primary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=3)
        
        # Analytics features
        tk.Label(insights_content, text=f"Financial Health: {health_score:.0f}/100", 
                font=(FONTS["body"][0], FONTS["body"][1], "bold"), fg=health_color, bg=COLORS["surface"]).pack(anchor=tk.W, pady=5)
        tk.Label(insights_content, text=f"Savings Rate: {savings_rate:.1f}%", 
                font=FONTS["body"], fg=COLORS["accent"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=3)
        
        # Smart insights
        if smart_insights:
            for insight in smart_insights[:2]:
                tk.Label(insights_content, text=insight, 
                        font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=2)
        
        # Budget alerts
        if budget_alerts:
            tk.Label(insights_content, text="Budget Alerts:", 
                    font=(FONTS["body"][0], FONTS["body"][1], "bold"), fg=COLORS["danger"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=(8, 3))
            for alert in budget_alerts[:2]:
                tk.Label(insights_content, text=alert, 
                        font=FONTS["small"], fg=COLORS["warning"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=2)


    def show_transactions(self):
        """Show transactions management"""
        self._set_view_state("transactions", "Transactions", "Manage expense and income records", "Transactions loaded")
        self.clear_content()
        
        create_header(self.content_frame, "Transactions", "Manage your income and expenses")

        action_bar = tk.Frame(self.content_frame, bg=COLORS["background"])
        action_bar.pack(fill=tk.X, padx=20, pady=(0, 6))
        tk.Button(
            action_bar,
            text="All Transactions Menu",
            command=self.open_all_transactions_menu,
            bg=COLORS["primary"],
            fg="white",
            font=FONTS["body"],
            relief=tk.FLAT,
            padx=14,
            pady=7,
            cursor="hand2",
        ).pack(side=tk.RIGHT, padx=(0, 8))
        tk.Button(
            action_bar,
            text="Import PDF Statement",
            command=self.import_statement_pdf,
            bg=COLORS["secondary"],
            fg="white",
            font=FONTS["body"],
            relief=tk.FLAT,
            padx=14,
            pady=7,
            cursor="hand2",
        ).pack(side=tk.RIGHT)
        
        
        # Tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Expenses tab
        expenses_frame = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(expenses_frame, text="Expenses")
        self.create_expense_manager(expenses_frame)
        
        # Income tab
        income_frame = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(income_frame, text="Income")
        self.create_income_manager(income_frame)

    def open_all_transactions_menu(self):
        """Open unified transaction explorer with account filter and edit support."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("All Transactions")
        dlg.geometry("1200x720")
        dlg.minsize(1000, 560)
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)

        outer = tk.Frame(dlg, bg=COLORS["background"])
        outer.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        controls = tk.Frame(outer, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        controls.pack(fill=tk.X, pady=(0, 10))

        accounts = self.db.get_managed_accounts(self.user_id)
        account_map = {"All Accounts": "ALL", "Personal (Main)": None}
        account_options = ["All Accounts", "Personal (Main)"]
        for acc in accounts:
            account_options.append(acc["account_name"])
            account_map[acc["account_name"]] = acc["id"]

        account_var = tk.StringVar(value="All Accounts")
        type_var = tk.StringVar(value="All")
        search_var = tk.StringVar(value="")

        tk.Label(controls, text="Account", font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"]).grid(row=0, column=0, padx=8, pady=10, sticky=tk.W)
        ttk.Combobox(controls, textvariable=account_var, values=account_options, width=24).grid(row=0, column=1, padx=6, pady=10, sticky=tk.W)
        tk.Label(controls, text="Type", font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"]).grid(row=0, column=2, padx=8, pady=10, sticky=tk.W)
        ttk.Combobox(controls, textvariable=type_var, values=["All", "Expense", "Income"], width=12).grid(row=0, column=3, padx=6, pady=10, sticky=tk.W)
        tk.Label(controls, text="Search", font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"]).grid(row=0, column=4, padx=8, pady=10, sticky=tk.W)
        search_entry = CustomEntry(controls, placeholder="Description/category/source")
        search_entry.grid(row=0, column=5, padx=6, pady=10, sticky=tk.W)
        controls.columnconfigure(5, weight=1)

        table_frame = tk.Frame(outer, bg=COLORS["background"])
        table_frame.pack(fill=tk.BOTH, expand=True)
        cols = ("Type", "ID", "Date", "Account", "Category/Source", "Amount", "Description", "Method")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        widths = {
            "Type": 80, "ID": 60, "Date": 100, "Account": 170,
            "Category/Source": 170, "Amount": 100, "Description": 370, "Method": 110
        }
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 120))
        self._attach_tree_sorting(tree, cols)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        summary_var = tk.StringVar(value="")
        tk.Label(outer, textvariable=summary_var, bg=COLORS["background"], fg=COLORS["text_secondary"], font=FONTS["small"]).pack(anchor=tk.W, pady=(8, 0))

        managed_lookup = {acc["id"]: acc["account_name"] for acc in accounts}

        def get_account_name(account_id):
            if account_id in (None, "", "None"):
                return "Personal (Main)"
            return managed_lookup.get(account_id, f"Account #{account_id}")

        rows_cache = []

        def load_rows():
            rows_cache.clear()
            selected_account = account_map.get(account_var.get(), "ALL")

            exp_rows = self.db.get_expenses(self.user_id)
            inc_rows = self.db.get_income(self.user_id)

            for e in exp_rows:
                if selected_account != "ALL" and e.get("account_id") != selected_account:
                    continue
                rows_cache.append({
                    "type": "Expense",
                    "id": e["id"],
                    "date": e.get("date", ""),
                    "account": get_account_name(e.get("account_id")),
                    "category_source": e.get("category", ""),
                    "amount": float(e.get("amount", 0)),
                    "description": e.get("description", "") or "-",
                    "method": e.get("payment_method", "") or "-",
                })

            for i in inc_rows:
                if selected_account != "ALL" and i.get("account_id") != selected_account:
                    continue
                rows_cache.append({
                    "type": "Income",
                    "id": i["id"],
                    "date": i.get("date", ""),
                    "account": get_account_name(i.get("account_id")),
                    "category_source": i.get("source", ""),
                    "amount": float(i.get("amount", 0)),
                    "description": i.get("description", "") or "-",
                    "method": "-",
                })

            rows_cache.sort(key=lambda r: r["date"], reverse=True)

        def render():
            tree.delete(*tree.get_children())
            selected_type = type_var.get().strip().lower()
            query = search_entry.get().strip().lower()
            shown = []
            for row in rows_cache:
                if selected_type != "all" and row["type"].lower() != selected_type:
                    continue
                if query:
                    hay = " ".join([
                        row["type"], str(row["id"]), row["date"], row["account"],
                        row["category_source"], row["description"], row["method"]
                    ]).lower()
                    if query not in hay:
                        continue
                shown.append(row)

            for idx, row in enumerate(shown):
                tree.insert("", "end", iid=str(idx), values=(
                    row["type"],
                    row["id"],
                    row["date"],
                    row["account"],
                    row["category_source"],
                    f"{row['amount']:.2f}",
                    row["description"][:90],
                    row["method"],
                ))
            summary_var.set(f"Showing {len(shown)} transaction(s). Double-click a row to edit.")
            return shown

        current_shown = []

        def refresh():
            nonlocal current_shown
            load_rows()
            current_shown = render()

        def on_double_click(event=None):
            sel = tree.selection()
            if not sel:
                return
            idx = int(sel[0])
            if idx < 0 or idx >= len(current_shown):
                return
            row = current_shown[idx]
            if row["type"] == "Expense":
                self.show_edit_expense_dialog(int(row["id"]))
            else:
                self.show_edit_income_dialog(int(row["id"]))

        tree.bind("<Double-1>", on_double_click)
        search_entry.entry.bind("<KeyRelease>", lambda e: render())
        search_entry.entry.bind("<Return>", lambda e: render())
        account_var.trace_add("write", lambda *_: refresh())
        type_var.trace_add("write", lambda *_: render())

        btns = tk.Frame(outer, bg=COLORS["background"])
        btns.pack(fill=tk.X, pady=(8, 0))
        tk.Button(btns, text="Refresh", command=refresh, bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.RIGHT, padx=6)
        tk.Button(btns, text="Close", command=dlg.destroy, bg=COLORS["text_secondary"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.RIGHT, padx=6)

        refresh()

    def show_edit_expense_dialog(self, expense_id):
        """Show edit expense dialog"""
        # Get expense data
        expenses = self.db.get_expenses(self.user_id)
        expense = next((e for e in expenses if e['id'] == expense_id), None)
        
        if not expense:
            show_message(self.parent, "Error", "Expense not found", "error")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Expense")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.config(bg=COLORS["background"])
        
        # Center dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=COLORS["background"])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Category
        tk.Label(form_frame, text="Category", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        category_var = tk.StringVar(value=expense['category'])
        categories = ["Food", "Transport", "Entertainment", "Utilities", "Healthcare", "Education", "Other"]
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, values=categories, width=30)
        category_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Amount
        tk.Label(form_frame, text="Amount", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        amount_entry = CustomEntry(form_frame)
        amount_entry.set(str(expense['amount']))
        amount_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Date
        tk.Label(form_frame, text="Date", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        date_entry = CustomEntry(form_frame)
        date_entry.set(expense['date'])
        date_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        tk.Button(
            form_frame,
            text="Pick",
            command=lambda: self._open_date_picker(date_entry),
            font=FONTS["small"],
            bg=COLORS["secondary"],
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4
        ).grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Description
        tk.Label(form_frame, text="Description", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        description_entry = CustomEntry(form_frame)
        description_entry.set(expense['description'] or "")
        description_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Payment method
        tk.Label(form_frame, text="Payment Method", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=4, column=0, sticky=tk.W, pady=5)
        
        payment_var = tk.StringVar(value=expense['payment_method'] or "")
        payment_combo = ttk.Combobox(form_frame, textvariable=payment_var, 
                                     values=["Cash", "Card", "UPI", "Other"], width=30)
        payment_combo.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg=COLORS["background"])
        btn_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        def update_expense():
            try:
                amount = float(amount_entry.get())
            except ValueError:
                show_message(dialog, "Error", "Invalid amount", "error")
                return
            
            self.db.update_expense(
                expense_id,
                category=category_var.get(),
                amount=amount,
                date=date_entry.get(),
                description=description_entry.get(),
                payment_method=payment_var.get()
            )
            show_message(dialog, "Success", "Expense updated successfully", "info")
            dialog.destroy()
            self.show_transactions()
        
        update_btn = tk.Button(btn_frame, text="Update", command=update_expense,
                              font=FONTS["body"], bg=COLORS["primary"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        update_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                              font=FONTS["body"], bg=COLORS["text_secondary"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(btn_frame, text="Delete", command=lambda: self.delete_expense(expense_id, dialog),
                              font=FONTS["body"], bg=COLORS["danger"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        delete_btn.pack(side=tk.RIGHT, padx=5)

    def delete_expense(self, expense_id, dialog):
        """Delete an expense with confirmation"""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            row = self.db.get_expense_by_id(expense_id)
            if row:
                self.db.trash_item(self.user_id, "expense", row)
            self.db.delete_expense(expense_id)
            show_message(dialog, "Success", "Expense deleted successfully", "info")
            dialog.destroy()
            self.show_transactions()

    def show_edit_income_dialog(self, income_id):
        """Show edit income dialog"""
        # Get income data
        income_list = self.db.get_income(self.user_id)
        income = next((i for i in income_list if i['id'] == income_id), None)
        
        if not income:
            show_message(self.parent, "Error", "Income record not found", "error")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Income")
        dialog.geometry("500x350")
        dialog.resizable(False, False)
        dialog.config(bg=COLORS["background"])
        
        # Center dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Form
        form_frame = tk.Frame(dialog, bg=COLORS["background"])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Source
        tk.Label(form_frame, text="Source", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        source_entry = CustomEntry(form_frame)
        source_entry.set(income['source'])
        source_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Amount
        tk.Label(form_frame, text="Amount", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        amount_entry = CustomEntry(form_frame)
        amount_entry.set(str(income['amount']))
        amount_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Date
        tk.Label(form_frame, text="Date", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        date_entry = CustomEntry(form_frame)
        date_entry.set(income['date'])
        date_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        tk.Button(
            form_frame,
            text="Pick",
            command=lambda: self._open_date_picker(date_entry),
            font=FONTS["small"],
            bg=COLORS["secondary"],
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=4
        ).grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Description
        tk.Label(form_frame, text="Description", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["background"]).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        description_entry = CustomEntry(form_frame)
        description_entry.set(income.get('description') or "")
        description_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        
        form_frame.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg=COLORS["background"])
        btn_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        def update_income():
            try:
                amount = float(amount_entry.get())
            except ValueError:
                show_message(dialog, "Error", "Invalid amount", "error")
                return
            
            self.db.update_income(
                income_id,
                source=source_entry.get(),
                amount=amount,
                date=date_entry.get(),
                description=description_entry.get()
            )
            show_message(dialog, "Success", "Income updated successfully", "info")
            dialog.destroy()
            self.show_transactions()
        
        update_btn = tk.Button(btn_frame, text="Update", command=update_income,
                              font=FONTS["body"], bg=COLORS["primary"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        update_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                              font=FONTS["body"], bg=COLORS["text_secondary"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(btn_frame, text="Delete", command=lambda: self.delete_income(income_id, dialog),
                              font=FONTS["body"], bg=COLORS["danger"], fg="white",
                              relief=tk.FLAT, padx=20, pady=8)
        delete_btn.pack(side=tk.RIGHT, padx=5)

    def delete_income(self, income_id, dialog):
        """Delete income with confirmation"""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this income?"):
            row = self.db.get_income_by_id(income_id)
            if row:
                self.db.trash_item(self.user_id, "income", row)
            self.db.delete_income(income_id)
            show_message(dialog, "Success", "Income deleted successfully", "info")
            dialog.destroy()
            self.show_transactions()


    def create_expense_manager(self, parent):
        """Create expense management interface"""
        # Input section
        input_frame = tk.Frame(parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        input_frame.pack(fill=tk.X, padx=15, pady=15)
        
        title_frame = tk.Frame(input_frame, bg=COLORS["surface"])
        title_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            title_frame,
            text="Add New Expense",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        form_frame = tk.Frame(input_frame, bg=COLORS["surface"])
        form_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Category
        tk.Label(form_frame, text="Category", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        category_var = tk.StringVar()
        categories = ["Food", "Transport", "Entertainment", "Utilities", "Healthcare", "Education", "Other"]
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, values=categories, width=20)
        category_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Amount
        tk.Label(form_frame, text="Amount", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        amount_entry = CustomEntry(form_frame, placeholder="0.00")
        amount_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # Date
        tk.Label(form_frame, text="Date", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        date_entry = CustomEntry(form_frame, placeholder="YYYY-MM-DD")
        date_entry.set(str(datetime.now().date()))
        date_entry.grid(row=0, column=5, sticky=tk.EW, padx=5, pady=5)
        tk.Button(
            form_frame,
            text="Pick",
            command=lambda: self._open_date_picker(date_entry),
            font=FONTS["small"],
            bg=COLORS["secondary"],
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=5
        ).grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        tk.Button(
            form_frame,
            text="Pick",
            command=lambda: self._open_date_picker(date_entry),
            font=FONTS["small"],
            bg=COLORS["secondary"],
            fg="white",
            relief=tk.FLAT,
            padx=8,
            pady=5
        ).grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        
        # Description
        tk.Label(form_frame, text="Description", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        description_entry = CustomEntry(form_frame, placeholder="Optional description")
        description_entry.grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        suggestion_var = tk.StringVar(value="Smart category: none")
        tk.Label(
            form_frame,
            textvariable=suggestion_var,
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"]
        ).grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Payment method
        tk.Label(form_frame, text="Payment Method", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        payment_var = tk.StringVar()
        payment_combo = ttk.Combobox(form_frame, textvariable=payment_var, 
                                     values=["Cash", "Card", "UPI", "Other"], width=20)
        payment_combo.grid(row=1, column=4, columnspan=2, sticky=tk.EW, padx=5, pady=5)
        
        # Account selector (for managed accounts)
        tk.Label(form_frame, text="Account", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        account_var = tk.StringVar()
        accounts = self.db.get_managed_accounts(self.user_id)
        account_list = ["Personal (Main)"] + [acc['account_name'] for acc in accounts]
        account_map = {"Personal (Main)": None}
        for acc in accounts:
            account_map[acc['account_name']] = acc['id']
        
        account_combo = ttk.Combobox(form_frame, textvariable=account_var, values=account_list, width=20)
        account_combo.set("Personal (Main)")
        account_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

        # Attachment + receipt scan
        attachment_var = tk.StringVar(value="")
        attachment_label_var = tk.StringVar(value="No receipt attached")
        tk.Label(form_frame, text="Receipt", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=2, column=4, sticky=tk.W, padx=5, pady=5)
        tk.Label(form_frame, textvariable=attachment_label_var, font=FONTS["small"],
                fg=COLORS["text_secondary"], bg=COLORS["surface"]).grid(row=2, column=5, sticky=tk.W, padx=5, pady=5)
        
        form_frame.columnconfigure((1, 3, 4), weight=1)

        def apply_smart_category(event=None):
            desc = description_entry.get().strip()
            if not desc:
                suggestion_var.set("Smart category: none")
                return
            suggested = self._smart_suggest_category(desc)
            if suggested:
                category_var.set(suggested)
                suggestion_var.set(f"Smart category: {suggested}")
            else:
                suggestion_var.set("Smart category: none")

        description_entry.entry.bind("<KeyRelease>", apply_smart_category)

        def choose_attachment():
            path = filedialog.askopenfilename(
                title="Choose Receipt/Invoice",
                filetypes=[("Image/PDF", "*.png *.jpg *.jpeg *.bmp *.pdf"), ("All files", "*.*")]
            )
            if path:
                attachment_var.set(path)
                attachment_label_var.set(os.path.basename(path))

        def scan_receipt_ocr():
            path = filedialog.askopenfilename(
                title="Scan Receipt",
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")]
            )
            if not path:
                return
            text = self._extract_receipt_text(path)
            if not text.strip():
                show_message(self.parent, "Info", "OCR could not extract text. Install pytesseract + pillow for best results.", "info")
                return
            parsed = self._parse_receipt_data(text)
            if parsed.get("amount") is not None:
                amount_entry.set(str(parsed["amount"]))
            if parsed.get("date"):
                date_entry.set(parsed["date"])
            if parsed.get("category"):
                category_var.set(parsed["category"])
            attachment_var.set(path)
            attachment_label_var.set(os.path.basename(path))
            self.set_status("Receipt scanned with OCR", auto_clear=True)
        
        # Add button
        def add_expense():
            category = category_var.get()
            amount = amount_entry.get()
            date = date_entry.get()
            description = description_entry.get()
            payment = payment_var.get()
            
            if not all([category, amount, date]):
                show_message(self.parent, "Error", "Please fill required fields", "error")
                return
            
            try:
                amount = float(amount)
            except ValueError:
                show_message(self.parent, "Error", "Invalid amount", "error")
                return
            
            # Get selected account ID
            selected_account = account_var.get()
            account_id = account_map.get(selected_account)
            
            self.db.add_expense(
                self.user_id,
                category,
                amount,
                date,
                description,
                payment,
                account_id=account_id,
                attachment_path=attachment_var.get() or None
            )
            self.set_status(f"Expense added: {category} ({format_currency(amount)})", auto_clear=True)
            show_message(self.parent, "Success", "Expense added successfully", "info")
            
            # Clear form
            category_var.set("")
            amount_entry.clear()
            date_entry.set(str(datetime.now().date()))
            description_entry.clear()
            payment_var.set("")
            account_var.set("Personal (Main)")
            attachment_var.set("")
            attachment_label_var.set("No receipt attached")
            
            # Refresh data
            self.show_transactions()
        
        add_btn = tk.Button(
            form_frame,
            text="Add Expense",
            command=add_expense,
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        add_btn.grid(row=3, column=5, sticky=tk.E, padx=5, pady=15)
        tk.Button(form_frame, text="Attach", command=choose_attachment, font=FONTS["small"],
                 bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=10, pady=5).grid(row=3, column=3, sticky=tk.W, padx=5, pady=10)
        tk.Button(form_frame, text="OCR Scan", command=scan_receipt_ocr, font=FONTS["small"],
                 bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=10, pady=5).grid(row=3, column=4, sticky=tk.W, padx=5, pady=10)
        
        # List section
        list_frame = tk.Frame(parent, bg=COLORS["background"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with search
        header_frame = tk.Frame(list_frame, bg=COLORS["background"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="Recent Expenses",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["background"]
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        summary_var = tk.StringVar(value="0 expenses shown | Total: 0.00")
        tk.Label(
            header_frame,
            textvariable=summary_var,
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["background"]
        ).pack(side=tk.LEFT, padx=(12, 0))

        search_label = tk.Label(header_frame, text="Search:", font=FONTS["body"],
                               fg=COLORS["text_primary"], bg=COLORS["background"])
        search_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        search_entry = CustomEntry(header_frame, placeholder="Search expenses...")
        search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Table
        columns = ("ID", "Date", "Category", "Amount", "Description", "Method", "Actions")
        tree = ttk.Treeview(list_frame, columns=columns, height=12, show="headings")
        
        col_widths = {"ID": 30, "Date": 80, "Category": 100, "Amount": 80, "Description": 120, "Method": 70, "Actions": 100}
        for col in columns:
            tree.column(col, width=col_widths.get(col, 100))
        self._attach_tree_sorting(tree, columns)
        
        # Get expenses
        expenses = self.db.get_expenses(self.user_id)

        def render_expenses(data):
            tree.delete(*tree.get_children())
            for exp in data:
                tree.insert("", "end", values=(
                    exp['id'],
                    exp['date'],
                    exp['category'],
                    f"{exp['amount']:.2f}",
                    exp['description'][:30] if exp['description'] else "-",
                    exp['payment_method'] or "-",
                    "Double-click to edit"
                ), tags=(f"expense_{exp['id']}",))
            total = sum(float(exp.get('amount', 0)) for exp in data)
            summary_var.set(f"{len(data)} expenses shown | Total: {format_currency(total)}")

        render_expenses(expenses)

        def filter_expenses(event=None):
            query = search_entry.get().strip().lower()
            if not query:
                render_expenses(expenses)
                return
            filtered = []
            for exp in expenses:
                values = (
                    exp.get('id'),
                    exp.get('date'),
                    exp.get('category'),
                    exp.get('amount'),
                    exp.get('description'),
                    exp.get('payment_method')
                )
                if self._row_matches_search(values, query):
                    filtered.append(exp)
            render_expenses(filtered)

        search_entry.entry.bind("<KeyRelease>", filter_expenses)
        search_entry.entry.bind("<Return>", filter_expenses)
        
        # Bind double-click for editing
        def on_tree_double_click(event):
            item = tree.selection()[0] if tree.selection() else None
            if item:
                values = tree.item(item, 'values')
                exp_id = int(values[0])  # Convert string to int for database lookup
                self.show_edit_expense_dialog(exp_id)
        
        tree.bind("<Double-1>", on_tree_double_click)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_income_manager(self, parent):
        """Create income management interface"""
        # Input section
        input_frame = tk.Frame(parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        input_frame.pack(fill=tk.X, padx=15, pady=15)
        
        title_frame = tk.Frame(input_frame, bg=COLORS["surface"])
        title_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(
            title_frame,
            text="Add Income",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["surface"]
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        form_frame = tk.Frame(input_frame, bg=COLORS["surface"])
        form_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Source
        tk.Label(form_frame, text="Source", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        source_entry = CustomEntry(form_frame, placeholder="Income source")
        source_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Amount
        tk.Label(form_frame, text="Amount", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        amount_entry = CustomEntry(form_frame, placeholder="0.00")
        amount_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=5)
        
        # Date
        tk.Label(form_frame, text="Date", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        date_entry = CustomEntry(form_frame, placeholder="YYYY-MM-DD")
        date_entry.set(str(datetime.now().date()))
        date_entry.grid(row=0, column=5, sticky=tk.EW, padx=5, pady=5)
        
        # Description
        tk.Label(form_frame, text="Description", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        description_entry = CustomEntry(form_frame, placeholder="Optional")
        description_entry.grid(row=1, column=1, columnspan=4, sticky=tk.EW, padx=5, pady=5)
        
        # Account selector (for managed accounts)
        tk.Label(form_frame, text="Account", font=FONTS["body"],
                fg=COLORS["text_primary"], bg=COLORS["surface"]).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        account_var = tk.StringVar()
        accounts = self.db.get_managed_accounts(self.user_id)
        account_list = ["Personal (Main)"] + [acc['account_name'] for acc in accounts]
        account_map = {"Personal (Main)": None}
        for acc in accounts:
            account_map[acc['account_name']] = acc['id']
        
        account_combo = ttk.Combobox(form_frame, textvariable=account_var, values=account_list, width=20)
        account_combo.set("Personal (Main)")
        account_combo.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        form_frame.columnconfigure((1, 3, 4), weight=1)
        
        # Add button
        def add_income():
            source = source_entry.get()
            amount = amount_entry.get()
            date = date_entry.get()
            description = description_entry.get()
            
            if not all([source, amount, date]):
                show_message(self.parent, "Error", "Please fill required fields", "error")
                return
            
            try:
                amount = float(amount)
            except ValueError:
                show_message(self.parent, "Error", "Invalid amount", "error")
                return
            
            # Get selected account ID
            selected_account = account_var.get()
            account_id = account_map.get(selected_account)
            
            self.db.add_income(self.user_id, source, amount, date, description, account_id=account_id)
            self.set_status(f"Income added: {source} ({format_currency(amount)})", auto_clear=True)
            show_message(self.parent, "Success", "Income added successfully", "info")
            
            # Clear form and refresh
            source_entry.clear()
            amount_entry.clear()
            date_entry.set(str(datetime.now().date()))
            description_entry.clear()
            account_var.set("Personal (Main)")
            
            # Refresh
            self.show_transactions()
        
        add_btn = tk.Button(
            form_frame,
            text="Add Income",
            command=add_income,
            font=FONTS["body"],
            bg=COLORS["accent"],
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        add_btn.grid(row=3, column=5, sticky=tk.E, padx=5, pady=15)
        
        # List section
        list_frame = tk.Frame(parent, bg=COLORS["background"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with search
        header_frame = tk.Frame(list_frame, bg=COLORS["background"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            header_frame,
            text="Income Records",
            font=FONTS["subheading"],
            fg=COLORS["text_primary"],
            bg=COLORS["background"]
        ).pack(side=tk.LEFT, anchor=tk.W)
        
        summary_var = tk.StringVar(value="0 income records shown | Total: 0.00")
        tk.Label(
            header_frame,
            textvariable=summary_var,
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["background"]
        ).pack(side=tk.LEFT, padx=(12, 0))

        search_label = tk.Label(header_frame, text="Search:", font=FONTS["body"],
                               fg=COLORS["text_primary"], bg=COLORS["background"])
        search_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        search_entry = CustomEntry(header_frame, placeholder="Search income...")
        search_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Table
        columns = ("ID", "Date", "Source", "Amount", "Description", "Actions")
        tree = ttk.Treeview(list_frame, columns=columns, height=12, show="headings")
        
        col_widths = {"ID": 30, "Date": 80, "Source": 100, "Amount": 100, "Description": 150, "Actions": 100}
        for col in columns:
            tree.column(col, width=col_widths.get(col, 100))
        self._attach_tree_sorting(tree, columns)
        
        # Get income
        income = self.db.get_income(self.user_id)

        def render_income(data):
            tree.delete(*tree.get_children())
            for inc in data:
                tree.insert("", "end", values=(
                    inc['id'],
                    inc['date'],
                    inc['source'],
                    f"{inc['amount']:.2f}",
                    inc['description'][:30] if inc.get('description') else "-",
                    "Double-click to edit"
                ), tags=(f"income_{inc['id']}",))
            total = sum(float(inc.get('amount', 0)) for inc in data)
            summary_var.set(f"{len(data)} income records shown | Total: {format_currency(total)}")

        render_income(income)

        def filter_income(event=None):
            query = search_entry.get().strip().lower()
            if not query:
                render_income(income)
                return
            filtered = []
            for inc in income:
                values = (
                    inc.get('id'),
                    inc.get('date'),
                    inc.get('source'),
                    inc.get('amount'),
                    inc.get('description')
                )
                if self._row_matches_search(values, query):
                    filtered.append(inc)
            render_income(filtered)

        search_entry.entry.bind("<KeyRelease>", filter_income)
        search_entry.entry.bind("<Return>", filter_income)
        
        # Bind double-click for editing
        def on_tree_double_click(event):
            item = tree.selection()[0] if tree.selection() else None
            if item:
                values = tree.item(item, 'values')
                inc_id = int(values[0])  # Convert string to int for database lookup
                self.show_edit_income_dialog(inc_id)
        
        tree.bind("<Double-1>", on_tree_double_click)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_accounts(self):
        """Show account management section"""
        self._set_view_state("accounts", "Manage Accounts", "Account entities and account-level analytics", "Accounts loaded")
        self.clear_content()
        
        create_header(self.content_frame, "People Accounts", "Manage accounts and track individual transactions")
        
        # Get managed accounts
        accounts = self.db.get_managed_accounts(self.user_id)
        
        # Button frame
        btn_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        add_btn = tk.Button(btn_frame, text="+ Add New Account", bg=COLORS["accent"], fg="white",
                           font=FONTS["body"], relief=tk.FLAT, cursor="hand2",
                           command=self.add_new_account)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Accounts container
        canvas = tk.Canvas(self.content_frame, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["background"])
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        if not accounts:
            tk.Label(scrollable_frame, text="No accounts yet. Create one to get started!",
                    font=FONTS["body"], fg=COLORS["text_secondary"],
                    bg=COLORS["background"]).pack(pady=50)
        else:
            for account in accounts:
                self.create_account_card(scrollable_frame, account)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")

    def create_account_card(self, parent, account):
        """Create account management card"""
        card = tk.Frame(parent, bg=COLORS["surface"], relief=tk.RIDGE, bd=2)
        card.pack(fill=tk.X, pady=12)
        
        # Header
        header = tk.Frame(card, bg=account.get('color', COLORS["primary"]), height=8)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Content
        content = tk.Frame(card, bg=COLORS["surface"])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Account info
        info_frame = tk.Frame(content, bg=COLORS["surface"])
        info_frame.pack(fill=tk.X, anchor=tk.W)
        
        tk.Label(info_frame, text=f"{account.get('icon', 'User')} {account['account_name']}", 
                font=FONTS["subheading"], fg=COLORS["primary"], 
                bg=COLORS["surface"]).pack(anchor=tk.W)
        
        if account.get('email'):
            tk.Label(info_frame, text=f"Email: {account['email']}", font=FONTS["small"],
                    fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=(3, 0))
        
        # Summary
        summary = self.db.get_account_summary(self.user_id, account['id'])
        
        summary_frame = tk.Frame(content, bg=COLORS["background"])
        summary_frame.pack(fill=tk.X, pady=(15, 10))
        
        tk.Label(summary_frame, text=f"Balance: Rs. {summary['balance']:,.2f}", 
                font=FONTS["body"], fg=COLORS["accent"],
                bg=COLORS["background"]).pack(anchor=tk.W, pady=3)
        
        tk.Label(summary_frame, text=f"Expenses: Rs. {summary['total_expenses']:,.2f}", 
                font=FONTS["small"], fg=COLORS["danger"],
                bg=COLORS["background"]).pack(anchor=tk.W, pady=1)
        
        # Action buttons
        btn_frame = tk.Frame(content, bg=COLORS["surface"])
        btn_frame.pack(fill=tk.X)
        
        view_btn = tk.Button(btn_frame, text="View Transactions", bg=COLORS["secondary"], fg="white",
                            font=FONTS["small"], relief=tk.FLAT, padx=10, pady=5,
                            command=lambda: self.view_account_transactions(account['id'], account['account_name']))
        view_btn.pack(side=tk.LEFT, padx=3)
        
        report_btn = tk.Button(btn_frame, text="Generate Report", bg=COLORS["accent"], fg="white",
                              font=FONTS["small"], relief=tk.FLAT, padx=10, pady=5,
                              command=lambda: self.generate_account_report(account['id'], account['account_name']))
        report_btn.pack(side=tk.LEFT, padx=3)
        
        edit_btn = tk.Button(btn_frame, text="Edit", bg=COLORS["warning"], fg="white",
                            font=FONTS["small"], relief=tk.FLAT, padx=10, pady=5,
                            command=lambda: self.edit_account(account['id']))
        edit_btn.pack(side=tk.LEFT, padx=3)
        
        del_btn = tk.Button(btn_frame, text="Delete", bg=COLORS["danger"], fg="white",
                           font=FONTS["small"], relief=tk.FLAT, padx=10, pady=5,
                           command=lambda: self.delete_account(account['id']))
        del_btn.pack(side=tk.LEFT, padx=3)

    def add_new_account(self):
        """Add new managed account"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add New Account")
        dialog.geometry("500x420")
        dialog.config(bg=COLORS["background"])
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Main frame with better layout
        main_frame = tk.Frame(dialog, bg=COLORS["background"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Top content area
        content_frame = tk.Frame(main_frame, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)
        
        # Account Name
        tk.Label(content_frame, text="Account Name *", font=FONTS["body"], fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 3))
        name_entry = tk.Entry(content_frame, font=FONTS["body"], width=40, bg=COLORS["surface"], fg=COLORS["text_primary"], relief=tk.FLAT, bd=1)
        name_entry.pack(fill=tk.X, pady=(0, 15), ipady=3)
        
        # Email
        tk.Label(content_frame, text="Email (optional)", font=FONTS["body"], fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 3))
        email_entry = tk.Entry(content_frame, font=FONTS["body"], width=40, bg=COLORS["surface"], fg=COLORS["text_primary"], relief=tk.FLAT, bd=1)
        email_entry.pack(fill=tk.X, pady=(0, 15), ipady=3)
        
        # Phone
        tk.Label(content_frame, text="Phone (optional)", font=FONTS["body"], fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 3))
        phone_entry = tk.Entry(content_frame, font=FONTS["body"], width=40, bg=COLORS["surface"], fg=COLORS["text_primary"], relief=tk.FLAT, bd=1)
        phone_entry.pack(fill=tk.X, pady=(0, 15), ipady=3)
        
        # Notes
        tk.Label(content_frame, text="Notes (optional)", font=FONTS["body"], fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 3))
        notes_entry = tk.Text(content_frame, font=FONTS["small"], height=3, width=40, bg=COLORS["surface"], fg=COLORS["text_primary"], relief=tk.FLAT, bd=1, wrap=tk.WORD)
        notes_entry.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Save and Cancel functions
        def save_account():
            name = name_entry.get().strip()
            if not name:
                show_message(dialog, "Error", "Account name is required", "error")
                return
            
            account_id = self.db.create_account(self.user_id, name, "Individual", 
                                              email_entry.get(), phone_entry.get(), 
                                              notes_entry.get("1.0", tk.END).strip())
            if account_id:
                show_message(dialog, "Success", "Account created successfully!", "info")
                dialog.destroy()
                self.show_accounts()
            else:
                show_message(dialog, "Error", "Failed to create account", "error")
        
        # Button frame at bottom
        btn_frame = tk.Frame(main_frame, bg=COLORS["background"])
        btn_frame.pack(fill=tk.X, padx=25, pady=(10, 20))
        
        save_btn = tk.Button(btn_frame, text="Save Account", bg=COLORS["accent"], fg="white", font=FONTS["body"], relief=tk.FLAT, padx=20, pady=8, command=save_account)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", bg=COLORS["secondary"], fg="white", font=FONTS["body"], relief=tk.FLAT, padx=20, pady=8, command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT)

    def view_account_transactions(self, account_id, account_name):
        """View transactions for specific account"""
        # Create window
        trans_window = tk.Toplevel(self.parent)
        trans_window.title(f"Transactions - {account_name}")
        trans_window.geometry("900x500")
        trans_window.config(bg=COLORS["background"])
        
        # Header
        header = tk.Frame(trans_window, bg=COLORS["background"])
        header.pack(fill=tk.X, padx=20, pady=15)
        
        tk.Label(header, text=f"Transactions for {account_name}",
                font=FONTS["heading"], fg=COLORS["primary"],
                bg=COLORS["background"]).pack(anchor=tk.W)
        
        # Table frame
        table_frame = tk.Frame(trans_window, bg=COLORS["background"])
        table_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Data
        expenses = self.db.get_account_expenses(self.user_id, account_id)
        
        # Table
        columns = ("Date", "Category", "Amount", "Description", "Method")
        tree = ttk.Treeview(table_frame, columns=columns, height=15, show="headings")
        
        col_widths = {"Date": 100, "Category": 120, "Amount": 100, "Description": 200, "Method": 100}
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths.get(col, 100))
        
        for exp in expenses:
            tree.insert("", "end", values=(
                exp['date'],
                exp['category'],
                f"Rs. {exp['amount']:.2f}",
                exp['description'][:30] if exp['description'] else "-",
                exp['payment_method'] or "-"
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary
        summary_frame = tk.Frame(trans_window, bg=COLORS["background"])
        summary_frame.pack(fill=tk.X, padx=20, pady=15)
        
        total = sum(e.get('amount', 0) for e in expenses)
        tk.Label(summary_frame, text=f"Total Expenses: Rs. {total:.2f}",
                font=FONTS["body"], fg=COLORS["primary"],
                bg=COLORS["background"]).pack(anchor=tk.E)

    def generate_account_report(self, account_id, account_name):
        """Generate report for specific account"""
        try:
            # Get account data
            account = self.db.get_account(account_id, self.user_id)
            if not account:
                show_message(self.parent, "Error", "Account not found", "error")
                return
            
            # Get account expenses
            expenses = self.db.get_account_expenses(self.user_id, account_id)
            if not expenses:
                show_message(self.parent, "Info", "No transactions found for this account", "info")
                return
            
            # Calculate summary
            summary = {
                'total_expense': sum(e.get('amount', 0) for e in expenses),
                'transaction_count': len(expenses),
                'date': datetime.now().strftime("%B %d, %Y")
            }
            
            # Get user data for report header
            user_data = self.db.get_user(self.user_id)
            
            # Generate PDF
            from pdf_generator import AccountingReportGenerator
            filename = f"Account_Report_{account_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_gen = AccountingReportGenerator(filename)
            
            # Create report content
            pdf_gen.generate_expense_report(
                user_data=user_data,
                expenses=expenses,
                summary=summary,
                start_date=expenses[-1]['date'] if expenses else datetime.now().strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            show_message(self.parent, "Success", f"Report saved as {filename}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to generate report: {str(e)}", "error")

    def edit_account(self, account_id):
        """Edit account details"""
        account = self.db.get_account(account_id, self.user_id)
        if not account:
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Edit Account")
        dialog.geometry("500x300")
        dialog.config(bg=COLORS["background"])
        
        content = tk.Frame(dialog, bg=COLORS["background"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content, text="Account Name", font=FONTS["body"],
                fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 5))
        name_entry = CustomEntry(content)
        name_entry.set(account['account_name'])
        name_entry.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(content, text="Email", font=FONTS["body"],
                fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 5))
        email_entry = CustomEntry(content)
        email_entry.set(account.get('email', ''))
        email_entry.pack(fill=tk.X, pady=(0, 15))
        
        def save_changes():
            self.db.update_account(account_id, self.user_id, 
                                  account_name=name_entry.get(), 
                                  email=email_entry.get())
            show_message(dialog, "Success", "Account updated!", "info")
            dialog.destroy()
            self.show_accounts()
            self.auto_save()
        
        btn_frame = tk.Frame(content, bg=COLORS["background"])
        btn_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(btn_frame, text="Save", bg=COLORS["accent"], fg="white",
                 font=FONTS["body"], relief=tk.FLAT, padx=20, pady=8,
                 command=save_changes).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", bg=COLORS["secondary"], fg="white",
                 font=FONTS["body"], relief=tk.FLAT, padx=20, pady=8,
                 command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def delete_account(self, account_id):
        """Delete managed account"""
        if messagebox.askyesno("Confirm", "Delete this account and all its transactions?"):
            if self.db.delete_account(account_id, self.user_id):
                show_message(self.parent, "Success", "Account deleted!", "info")
                self.show_accounts()
                self.auto_save()
            else:
                show_message(self.parent, "Error", "Failed to delete account", "error")

    def auto_save(self):
        """Auto-save functionality"""
        # Data is automatically saved to database on every operation
        # This can be extended for additional caching/sync operations
        pass

    def show_reports(self):
        """Show reports section"""
        self._set_view_state("reports", "Reports & Analytics", "Export, summarize, and present financial data", "Reports loaded")
        self.clear_content()
        
        create_header(self.content_frame, "Reports & Analytics", "Export and analyze your financial data")
        
        # Scrollable report options
        canvas = tk.Canvas(self.content_frame, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["background"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Report options
        reports_config = [
            {
                "title": "Expense Report - Monthly",
                "subtitle": "Detailed expense analysis for the past 30 days",
                "color": COLORS["primary"],
                "buttons": [("Export PDF", lambda: self.generate_expense_report("Month")),
                           ("Export CSV", lambda: self.export_expense_csv("Month")),
                           ("Email PDF", lambda: self.email_report("Month"))]
            },
            {
                "title": "Expense Report - Quarterly",
                "subtitle": "Analyze spending patterns over 90 days",
                "color": COLORS["secondary"],
                "buttons": [("Export PDF", lambda: self.generate_expense_report("Quarter")),
                           ("Export CSV", lambda: self.export_expense_csv("Quarter")),
                           ("Email PDF", lambda: self.email_report("Quarter"))]
            },
            {
                "title": "Annual Report",
                "subtitle": "Complete yearly financial summary and analysis",
                "color": COLORS["primary"],
                "buttons": [("Export PDF", lambda: self.generate_expense_report("Year")),
                           ("Export CSV", lambda: self.export_expense_csv("Year")),
                           ("Email PDF", lambda: self.email_report("Year"))]
            },
            {
                "title": "Balance Sheet",
                "subtitle": "Professional accounting statement with financial metrics",
                "color": COLORS["accent"],
                "buttons": [("Generate PDF", self.generate_balance_sheet),
                           ("View Summary", self.show_balance_summary),
                           ("Email PDF", lambda: self.email_report("Balance"))]
            },
            {
                "title": "Category Analysis",
                "subtitle": "Spending breakdown by expense categories",
                "color": COLORS["warning"],
                "buttons": [("View Chart", self.show_category_chart),
                           ("Export Data", lambda: self.export_category_data())]
            },
            {
                "title": "Data & Email Tools",
                "subtitle": "Configure SMTP, test email, and export full backup",
                "color": COLORS["secondary"],
                "buttons": [("Email Setup Help", self.show_email_setup_help),
                           ("Configure SMTP", self.configure_smtp_settings),
                           ("Send Test Email", self.send_test_email),
                           ("Export All Data", self.export_all_data_csv),
                           ("Export JSON", self.export_json_backup),
                           ("Import JSON", self.import_json_backup),
                           ("Backup DB", self.backup_database_copy),
                           ("Restore DB", self.restore_database_copy),
                           ("Subscriptions", self.open_subscription_center),
                           ("Invoice Generator", self.generate_invoice_pdf),
                           ("Report Designer", self.configure_report_designer),
                           ("Trash Bin", self.open_trash_bin),
                           ("Command Center", self.open_command_center),
                           ("Quick Calculator", self.show_quick_calculator),
                           ("Monthly Snapshot", self.generate_monthly_snapshot_txt),
                           ("Shortcuts Help", self.show_shortcuts_help)]
            }
        ]
        
        for report_config in reports_config:
            self.create_report_card(scrollable_frame, report_config)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")

    def create_report_card(self, parent, config):
        """Create a report card"""
        card = tk.Frame(parent, bg=COLORS["surface"], relief=tk.RIDGE, bd=2)
        card.pack(fill=tk.X, pady=15)
        
        # Header with color accent
        header = tk.Frame(card, bg=config["color"], height=8)
        header.pack(fill=tk.X)
        
        # Content
        content = tk.Frame(card, bg=COLORS["surface"])
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(
            content,
            text=config["title"],
            font=FONTS["subheading"],
            fg=COLORS["primary"],
            bg=COLORS["surface"]
        ).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(
            content,
            text=config["subtitle"],
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"]
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Buttons (responsive wrap layout)
        btn_frame = tk.Frame(content, bg=COLORS["surface"])
        btn_frame.pack(fill=tk.X)

        max_cols = 4
        for idx, (btn_text, btn_command) in enumerate(config["buttons"]):
            row = idx // max_cols
            col = idx % max_cols
            btn = tk.Button(
                btn_frame,
                text=btn_text,
                command=btn_command,
                font=FONTS["body"],
                bg=config["color"],
                fg="white",
                relief=tk.FLAT,
                padx=12,
                pady=8,
                cursor="hand2"
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=tk.EW)
            btn.bind("<Enter>", lambda e, b=btn, c=config: b.config(bg=self._lighten_color(c["color"])))
            btn.bind("<Leave>", lambda e, b=btn, c=config: b.config(bg=c["color"]))

        for c in range(max_cols):
            btn_frame.columnconfigure(c, weight=1)

    @staticmethod
    def _lighten_color(color):
        """Lighten a hex color"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c * 1.15)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def generate_expense_report(self, period):
        """Generate expense report PDF"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Expense_Report_{period}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if not file_path:
            return
        
        # Get date range
        if period == "Month":
            start_date = (datetime.now() - timedelta(days=30)).date()
        elif period == "Quarter":
            start_date = (datetime.now() - timedelta(days=90)).date()
        else:  # Year
            start_date = (datetime.now() - timedelta(days=365)).date()
        
        end_date = datetime.now().date()
        
        # Get data
        expenses = self.db.get_expenses(self.user_id, str(start_date), str(end_date))
        summary = self.db.get_summary(self.user_id, str(start_date), str(end_date))
        design = self.db.get_report_design(self.user_id) or {}
        report_user_data = dict(self.user_data)
        if design.get("brand_name"):
            report_user_data["full_name"] = design["brand_name"]
        
        # Generate PDF
        try:
            report = AccountingReportGenerator(file_path)
            report.generate_expense_report(
                report_user_data,
                expenses,
                summary,
                str(start_date),
                str(end_date)
            )
            show_message(self.parent, "Success", f"Report exported to {file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to generate report: {str(e)}", "error")

    def generate_balance_sheet(self):
        """Generate balance sheet PDF"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Balance_Sheet_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if not file_path:
            return
        
        # Get data
        income = self.db.get_income(self.user_id)
        expenses = self.db.get_expenses(self.user_id)
        summary = self.db.get_summary(self.user_id)
        design = self.db.get_report_design(self.user_id) or {}
        report_user_data = dict(self.user_data)
        if design.get("brand_name"):
            report_user_data["full_name"] = design["brand_name"]
        
        # Generate PDF
        try:
            report = AccountingReportGenerator(file_path)
            report.generate_balance_sheet(
                report_user_data,
                income,
                expenses,
                summary
            )
            show_message(self.parent, "Success", f"Balance Sheet exported to {file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to generate report: {str(e)}", "error")

    def show_email_setup_help(self):
        """Explain SMTP and how to configure email reports."""
        help_text = (
            "Email setup requires your email provider SMTP details.\n\n"
            "Recommended values:\n"
            "Gmail: server=smtp.gmail.com, port=587 (TLS)\n"
            "Outlook/Hotmail: server=smtp.office365.com, port=587 (TLS)\n"
            "Yahoo: server=smtp.mail.yahoo.com, port=587 (TLS)\n\n"
            "Important:\n"
            "1. Use your full email as SMTP Username.\n"
            "2. For Gmail/Outlook with 2FA, use an App Password (not your normal login password).\n"
            "3. Open Reports > Data & Email Tools > Configure SMTP first.\n"
            "4. Then use Send Test Email to verify before Email PDF."
        )
        messagebox.showinfo("Email Setup Guide", help_text)

    def configure_smtp_settings(self):
        """Collect and store SMTP settings for this app session."""
        server = simpledialog.askstring(
            "SMTP Setup",
            "SMTP Server (example: smtp.gmail.com)",
            initialvalue=self.smtp_settings.get("server", "smtp.gmail.com"),
        )
        if not server:
            return False

        port = simpledialog.askinteger(
            "SMTP Setup",
            "SMTP Port (587 for TLS, 465 for SSL)",
            initialvalue=int(self.smtp_settings.get("port", 587)),
            minvalue=1,
            maxvalue=65535,
        )
        if not port:
            return False

        username = simpledialog.askstring(
            "SMTP Setup",
            "SMTP Username (usually your full email)",
            initialvalue=self.smtp_settings.get("username", self.user_data.get("email", "")),
        )
        if not username or not validate_email(username):
            show_message(self.parent, "Error", "Enter a valid SMTP username email", "error")
            return False

        password = simpledialog.askstring(
            "SMTP Setup",
            "SMTP Password or App Password",
            show="*",
        )
        if not password:
            show_message(self.parent, "Error", "SMTP password is required", "error")
            return False

        use_tls = messagebox.askyesno(
            "SMTP Security",
            "Use TLS/STARTTLS?\nChoose Yes for port 587, No for port 465 (SSL).",
        )

        self.smtp_settings = {
            "server": server.strip(),
            "port": int(port),
            "username": username.strip(),
            "password": password,
            "use_tls": bool(use_tls),
        }
        self.set_status("SMTP settings saved for this session", auto_clear=True)
        show_message(self.parent, "Success", "SMTP settings saved", "info")
        return True

    def _send_email_message(self, msg):
        """Send an EmailMessage using configured SMTP settings."""
        s = self.smtp_settings
        if not all([s.get("server"), s.get("port"), s.get("username"), s.get("password")]):
            if not self.configure_smtp_settings():
                return False
            s = self.smtp_settings
        if not msg.get("From"):
            msg["From"] = s["username"]

        try:
            if s.get("use_tls", True):
                server = smtplib.SMTP(s["server"], int(s["port"]), timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                server = smtplib.SMTP_SSL(s["server"], int(s["port"]), timeout=20)

            server.login(s["username"], s["password"])
            server.send_message(msg)
            server.quit()
            return True
        except smtplib.SMTPAuthenticationError:
            show_message(
                self.parent,
                "Email Error",
                "SMTP login failed. Check username/password.\nIf using Gmail/Outlook with 2FA, use an App Password.",
                "error",
            )
        except Exception as e:
            show_message(self.parent, "Email Error", f"Failed to send email: {e}", "error")
        return False

    def send_test_email(self):
        """Send a test message to validate SMTP settings."""
        recipient = simpledialog.askstring(
            "Send Test Email",
            "Recipient Email:",
            initialvalue=self.user_data.get("email", ""),
        )
        if not recipient or not validate_email(recipient):
            show_message(self.parent, "Error", "Invalid recipient email", "error")
            return

        msg = EmailMessage()
        msg["Subject"] = "OG CA - SMTP Test"
        msg["From"] = self.smtp_settings.get("username", self.user_data.get("email", ""))
        msg["To"] = recipient.strip()
        msg.set_content(
            "This is a test email from OG CA.\n"
            "If you received this, your SMTP setup is working."
        )

        if self._send_email_message(msg):
            self.set_status("Test email sent", auto_clear=True)
            show_message(self.parent, "Success", "Test email sent successfully", "info")

    def email_report(self, period):
        """Generate a PDF report and email it as attachment."""
        file_path = None
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            file_path = tmp.name
            tmp.close()
            design = self.db.get_report_design(self.user_id) or {}
            report_user_data = dict(self.user_data)
            if design.get("brand_name"):
                report_user_data["full_name"] = design["brand_name"]

            if period in ("Month", "Quarter", "Year"):
                if period == "Month":
                    start_date = (datetime.now() - timedelta(days=30)).date()
                elif period == "Quarter":
                    start_date = (datetime.now() - timedelta(days=90)).date()
                else:
                    start_date = (datetime.now() - timedelta(days=365)).date()

                end_date = datetime.now().date()
                expenses = self.db.get_expenses(self.user_id, str(start_date), str(end_date))
                summary = self.db.get_summary(self.user_id, str(start_date), str(end_date))
                report = AccountingReportGenerator(file_path)
                report.generate_expense_report(
                    report_user_data, expenses, summary, str(start_date), str(end_date)
                )
                subject = f"{period} Expense Report"
            elif period == "Balance":
                income = self.db.get_income(self.user_id)
                expenses = self.db.get_expenses(self.user_id)
                summary = self.db.get_summary(self.user_id)
                report = AccountingReportGenerator(file_path)
                report.generate_balance_sheet(report_user_data, income, expenses, summary)
                subject = "Balance Sheet"
            else:
                raise ValueError("Unsupported report type")

            recipient = simpledialog.askstring(
                "Email Report",
                "Recipient Email:",
                initialvalue=self.user_data.get("email", ""),
            )
            if not recipient or not validate_email(recipient):
                show_message(self.parent, "Error", "Invalid recipient email", "error")
                return

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.smtp_settings.get("username", self.user_data.get("email", ""))
            msg["To"] = recipient.strip()
            msg.set_content("Please find attached your requested report.")

            with open(file_path, "rb") as f:
                data = f.read()
                attach_name = f"{subject.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                msg.add_attachment(data, maintype="application", subtype="pdf", filename=attach_name)

            if self._send_email_message(msg):
                self.set_status("Report emailed successfully", auto_clear=True)
                show_message(self.parent, "Success", "Report emailed successfully", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to prepare email report: {e}", "error")
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass

    def export_expense_csv(self, period):
        """Export expenses to CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"Expenses_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not file_path:
            return
        
        # Get date range
        if period == "Month":
            start_date = (datetime.now() - timedelta(days=30)).date()
        elif period == "Quarter":
            start_date = (datetime.now() - timedelta(days=90)).date()
        else:
            start_date = (datetime.now() - timedelta(days=365)).date()
        
        end_date = datetime.now().date()
        
        # Get expenses
        expenses = self.db.get_expenses(self.user_id, str(start_date), str(end_date))
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Category', 'Amount', 'Description', 'Payment Method', 'Notes'])
                
                for exp in expenses:
                    writer.writerow([
                        exp['date'],
                        exp['category'],
                        f"{exp['amount']:.2f}",
                        exp['description'] or '',
                        exp['payment_method'] or '',
                        exp['notes'] or ''
                    ])
                
                # Add summary
                writer.writerow([])
                total = sum(e['amount'] for e in expenses)
                writer.writerow(['TOTAL EXPENSES', '', f"{total:.2f}"])
            
            show_message(self.parent, "Success", f"Expenses exported to {file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to export CSV: {str(e)}", "error")

    def export_all_data_csv(self):
        """Export complete expense and income data into one CSV file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"All_Data_Backup_{datetime.now().strftime('%Y%m%d')}.csv",
        )
        if not file_path:
            return

        expenses = self.db.get_expenses(self.user_id)
        income = self.db.get_income(self.user_id)
        summary = self.db.get_summary(self.user_id)

        try:
            import csv

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["EXPENSE TRACKER DATA EXPORT"])
                writer.writerow([f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])

                writer.writerow(["SUMMARY"])
                writer.writerow(["Total Income", f"{summary['total_income']:.2f}"])
                writer.writerow(["Total Expenses", f"{summary['total_expenses']:.2f}"])
                writer.writerow(["Net Balance", f"{summary['balance']:.2f}"])
                writer.writerow([])

                writer.writerow(["EXPENSES"])
                writer.writerow(["Date", "Category", "Amount", "Description", "Payment Method", "Notes"])
                for exp in expenses:
                    writer.writerow([
                        exp.get("date", ""),
                        exp.get("category", ""),
                        f"{float(exp.get('amount', 0)):.2f}",
                        exp.get("description", "") or "",
                        exp.get("payment_method", "") or "",
                        exp.get("notes", "") or "",
                    ])
                writer.writerow([])

                writer.writerow(["INCOME"])
                writer.writerow(["Date", "Source", "Amount", "Description", "Notes"])
                for inc in income:
                    writer.writerow([
                        inc.get("date", ""),
                        inc.get("source", ""),
                        f"{float(inc.get('amount', 0)):.2f}",
                        inc.get("description", "") or "",
                        inc.get("notes", "") or "",
                    ])

            self.set_status("Full data backup exported", auto_clear=True)
            show_message(self.parent, "Success", f"All data exported to {file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to export all data: {str(e)}", "error")

    def export_json_backup(self):
        """Export all core data to a JSON backup file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile=f"OGCA_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )
        if not file_path:
            return

        payload = {
            "app": "OG CA",
            "version": "major-update",
            "generated_at": datetime.now().isoformat(),
            "user_id": self.user_id,
            "user": self.db.get_user(self.user_id),
            "expenses": self.db.get_expenses(self.user_id),
            "income": self.db.get_income(self.user_id),
            "summary": self.db.get_summary(self.user_id),
            "categories": self.db.get_category_summary(self.user_id),
        }

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            self.set_status("JSON backup exported", auto_clear=True)
            show_message(self.parent, "Success", f"JSON backup saved:\n{file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to export JSON: {e}", "error")

    def import_json_backup(self):
        """Import data from JSON backup (adds transactions to current account)."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Select JSON Backup",
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "Confirm Import",
            "This will add transactions from the backup into your current account.\nContinue?",
        ):
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            imported_expenses = 0
            for exp in data.get("expenses", []):
                self.db.add_expense(
                    self.user_id,
                    exp.get("category", "Other"),
                    float(exp.get("amount", 0)),
                    exp.get("date", str(datetime.now().date())),
                    exp.get("description", ""),
                    exp.get("payment_method", ""),
                    exp.get("notes", ""),
                    account_id=exp.get("account_id"),
                )
                imported_expenses += 1

            imported_income = 0
            for inc in data.get("income", []):
                self.db.add_income(
                    self.user_id,
                    inc.get("source", "Other"),
                    float(inc.get("amount", 0)),
                    inc.get("date", str(datetime.now().date())),
                    inc.get("description", ""),
                    inc.get("notes", ""),
                    account_id=inc.get("account_id"),
                )
                imported_income += 1

            self.load_data()
            self.refresh_current_page()
            self.set_status("JSON backup imported", auto_clear=True)
            show_message(
                self.parent,
                "Success",
                f"Import completed.\nExpenses: {imported_expenses}\nIncome: {imported_income}",
                "info",
            )
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to import JSON backup: {e}", "error")

    def backup_database_copy(self):
        """Create a direct copy of the SQLite database file."""
        src = os.path.join(os.path.dirname(__file__), "expense_tracker.db")
        if not os.path.exists(src):
            show_message(self.parent, "Error", "Database file not found", "error")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
            initialfile=f"OGCA_DB_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        )
        if not file_path:
            return

        try:
            shutil.copy2(src, file_path)
            self.set_status("Database backup created", auto_clear=True)
            show_message(self.parent, "Success", f"Database backup saved:\n{file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to backup database: {e}", "error")

    def restore_database_copy(self):
        """Restore DB from backup .db file."""
        src = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")], title="Select DB Backup")
        if not src:
            return

        dst = os.path.join(os.path.dirname(__file__), "expense_tracker.db")
        if not messagebox.askyesno(
            "Confirm Restore",
            "This will replace current database and restart the app data view.\nContinue?",
        ):
            return

        try:
            shutil.copy2(src, dst)
            self.load_data()
            self.refresh_current_page()
            self.set_status("Database restored", auto_clear=True)
            show_message(self.parent, "Success", "Database restored successfully", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to restore database: {e}", "error")

    def show_quick_calculator(self):
        """Simple built-in calculator utility."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("OG CA Calculator")
        dlg.geometry("420x180")
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)

        frm = tk.Frame(dlg, bg=COLORS["background"])
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        tk.Label(frm, text="Enter expression (e.g. 1200+340-50*2)", bg=COLORS["background"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(anchor=tk.W)
        entry = CustomEntry(frm)
        entry.pack(fill=tk.X, pady=8)
        result_var = tk.StringVar(value="Result: ")
        tk.Label(frm, textvariable=result_var, bg=COLORS["background"], fg=COLORS["primary"], font=FONTS["subheading"]).pack(anchor=tk.W, pady=8)

        def calc():
            expr = entry.get().strip()
            if not expr:
                return
            try:
                val = eval(expr, {"__builtins__": {}}, {})
                result_var.set(f"Result: {val}")
            except Exception:
                result_var.set("Result: Invalid expression")

        tk.Button(frm, text="Calculate", command=calc, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=16, pady=6).pack(anchor=tk.E)

    def generate_monthly_snapshot_txt(self):
        """Generate a lightweight monthly snapshot text file."""
        now = datetime.now()
        start = datetime(now.year, now.month, 1).date()
        end = now.date()
        expenses = self.db.get_expenses(self.user_id, str(start), str(end))
        income = self.db.get_income(self.user_id, str(start), str(end))
        summary = self.db.get_summary(self.user_id, str(start), str(end))

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"OGCA_Snapshot_{now.strftime('%Y_%m')}.txt",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("OG CA - Monthly Snapshot\n")
                f.write(f"Period: {start} to {end}\n\n")
                f.write(f"Total Income: {summary['total_income']:.2f}\n")
                f.write(f"Total Expenses: {summary['total_expenses']:.2f}\n")
                f.write(f"Net Balance: {summary['balance']:.2f}\n\n")
                f.write(f"Transactions: expenses={len(expenses)}, income={len(income)}\n")
            self.set_status("Monthly snapshot generated", auto_clear=True)
            show_message(self.parent, "Success", f"Snapshot saved:\n{file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to generate snapshot: {e}", "error")

    def show_shortcuts_help(self):
        """Display keyboard shortcuts."""
        messagebox.showinfo(
            "OG CA Shortcuts",
            "Ctrl+1 Dashboard\n"
            "Ctrl+2 Transactions\n"
            "Ctrl+3 Reports\n"
            "Ctrl+4 Accounts\n"
            "Ctrl+N Quick Expense\n"
            "Ctrl+Shift+N Quick Income\n"
            "F5 Refresh Current Page",
        )

    def open_command_center(self):
        """Open quick command launcher."""
        dlg = tk.Toplevel(self.parent)
        dlg.title("OG CA Command Center")
        dlg.geometry("520x340")
        dlg.config(bg=COLORS["background"])
        dlg.transient(self.parent)

        content = tk.Frame(dlg, bg=COLORS["background"])
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        tk.Label(content, text="Command Center", font=FONTS["heading"], fg=COLORS["primary"], bg=COLORS["background"]).pack(anchor=tk.W, pady=(0, 10))

        commands = [
            ("Go Dashboard", self.show_dashboard),
            ("Go Transactions", self.show_transactions),
            ("Go Reports", self.show_reports),
            ("Quick Add Expense", self.quick_add_expense),
            ("Quick Add Income", self.quick_add_income),
            ("Export JSON Backup", self.export_json_backup),
            ("Backup Database", self.backup_database_copy),
            ("Send Test Email", self.send_test_email),
            ("Open Calculator", self.show_quick_calculator),
        ]
        for text, cmd in commands:
            tk.Button(
                content,
                text=text,
                command=cmd,
                bg=COLORS["surface"],
                fg=COLORS["text_primary"],
                relief=tk.FLAT,
                anchor="w",
                padx=10,
                pady=8,
                cursor="hand2"
            ).pack(fill=tk.X, pady=3)

    def export_category_data(self):
        """Export category breakdown to CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"Category_Analysis_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        
        if not file_path:
            return
        
        # Get category summary
        category_summary = self.db.get_category_summary(self.user_id)
        
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Category', 'Amount', 'Number of Transactions', '% of Total'])
                
                total = sum(c['total'] for c in category_summary)
                
                for cat in category_summary:
                    percentage = (cat['total'] / total * 100) if total > 0 else 0
                    writer.writerow([
                        cat['category'],
                        f"{cat['total']:.2f}",
                        cat['count'],
                        f"{percentage:.1f}%"
                    ])
                
                writer.writerow([])
                writer.writerow(['TOTAL', f"{total:.2f}", sum(c['count'] for c in category_summary), '100%'])
            
            show_message(self.parent, "Success", f"Category data exported to {file_path}", "info")
        except Exception as e:
            show_message(self.parent, "Error", f"Failed to export CSV: {str(e)}", "error")

    def show_category_chart(self):
        """Show category chart"""
        show_message(self.parent, "Feature", "Category chart will be displayed here. Coming in next update!", "info")

    def show_balance_summary(self):
        """Show balance summary dialog"""
        summary = self.db.get_summary(self.user_id)
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Balance Summary")
        dialog.geometry("400x300")
        dialog.config(bg=COLORS["background"])
        
        dialog.transient(self.parent)
        
        content = tk.Frame(dialog, bg=COLORS["background"])
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content, text="Financial Summary", font=FONTS["heading"],
                fg=COLORS["primary"], bg=COLORS["background"]).pack(pady=20)
        
        # Summary items
        items = [
            ("Total Income", summary['total_income'], COLORS["accent"]),
            ("Total Expenses", summary['total_expenses'], COLORS["danger"]),
            ("Net Balance", summary['balance'], COLORS["primary"])
        ]
        
        for label, value, color in items:
            frame = tk.Frame(content, bg=COLORS["surface"])
            frame.pack(fill=tk.X, pady=10)
            
            tk.Label(frame, text=label, font=FONTS["body"],
                    fg=COLORS["text_primary"], bg=COLORS["surface"]).pack(side=tk.LEFT, padx=15, pady=10)
            
            tk.Label(frame, text=f"Rs. {value:,.2f}", font=FONTS["heading"],
                    fg=color, bg=COLORS["surface"]).pack(side=tk.RIGHT, padx=15, pady=10)
        
        close_btn = tk.Button(content, text="Close", command=dialog.destroy,
                             font=FONTS["body"], bg=COLORS["primary"], fg="white",
                             relief=tk.FLAT, padx=20, pady=8)
        close_btn.pack(pady=20)

    def show_budget(self):
        """Show budget and recurring bills management."""
        self._set_view_state("budget", "Budget", "Budget planner and recurring bill control center", "Budget loaded")
        self.clear_content()
        create_header(self.content_frame, "Budget & Recurring", "Plan limits, manage recurring bills, and track alerts")

        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # ---------------- Budget Planner Tab ----------------
        budget_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(budget_tab, text="Budget Planner")

        controls = tk.Frame(budget_tab, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        controls.pack(fill=tk.X, pady=(0, 12))

        month_var = tk.IntVar(value=datetime.now().month)
        year_var = tk.IntVar(value=datetime.now().year)
        category_var = tk.StringVar()
        limit_entry = CustomEntry(controls, placeholder="0.00")

        default_categories = ["Food", "Transport", "Entertainment", "Utilities", "Healthcare", "Education", "Other"]
        existing_categories = [c["category"] for c in self.db.get_category_summary(self.user_id)]
        all_categories = sorted(set(default_categories + existing_categories))

        tk.Label(controls, text="Category", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).grid(row=0, column=0, padx=8, pady=10, sticky=tk.W)
        cat_combo = ttk.Combobox(controls, textvariable=category_var, values=all_categories, width=18)
        cat_combo.grid(row=0, column=1, padx=8, pady=10, sticky=tk.W)

        tk.Label(controls, text="Limit", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).grid(row=0, column=2, padx=8, pady=10, sticky=tk.W)
        limit_entry.grid(row=0, column=3, padx=8, pady=10, sticky=tk.W)

        tk.Label(controls, text="Month", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).grid(row=0, column=4, padx=8, pady=10, sticky=tk.W)
        tk.Spinbox(controls, from_=1, to=12, textvariable=month_var, width=6).grid(row=0, column=5, padx=4, pady=10, sticky=tk.W)
        tk.Label(controls, text="Year", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).grid(row=0, column=6, padx=8, pady=10, sticky=tk.W)
        tk.Spinbox(controls, from_=2000, to=2100, textvariable=year_var, width=8).grid(row=0, column=7, padx=4, pady=10, sticky=tk.W)

        budget_table_frame = tk.Frame(budget_tab, bg=COLORS["background"])
        budget_table_frame.pack(fill=tk.BOTH, expand=True)
        budget_columns = ("ID", "Category", "Limit", "Spent", "Remaining", "Usage %", "Status")
        budget_tree = ttk.Treeview(budget_table_frame, columns=budget_columns, show="headings", height=14)
        for col in budget_columns:
            budget_tree.heading(col, text=col)
            budget_tree.column(col, width=120 if col != "Category" else 160)
        self._attach_tree_sorting(budget_tree, budget_columns)
        budget_scroll = ttk.Scrollbar(budget_table_frame, orient="vertical", command=budget_tree.yview)
        budget_tree.configure(yscroll=budget_scroll.set)
        budget_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        budget_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_budget_table():
            budget_tree.delete(*budget_tree.get_children())
            rows = self.db.get_budget_vs_actual(self.user_id, month_var.get(), year_var.get())
            for r in rows:
                usage = float(r["usage_percent"])
                if usage >= 100:
                    status = "Exceeded"
                elif usage >= 80:
                    status = "Warning"
                else:
                    status = "Healthy"
                budget_tree.insert(
                    "",
                    "end",
                    values=(
                        "",
                        r["category"],
                        f"{r['limit_amount']:.2f}",
                        f"{r['spent']:.2f}",
                        f"{r['remaining']:.2f}",
                        f"{usage:.1f}",
                        status,
                    ),
                )

            # inject IDs from current month budget rows to enable delete
            raw = self.db.get_budgets(self.user_id, month_var.get(), year_var.get())
            id_map = {b["category"]: b["id"] for b in raw}
            for item in budget_tree.get_children():
                vals = list(budget_tree.item(item, "values"))
                vals[0] = id_map.get(vals[1], "")
                budget_tree.item(item, values=vals)

        def save_budget():
            if not category_var.get().strip():
                show_message(self.parent, "Error", "Select a category", "error")
                return
            try:
                limit_amount = float(limit_entry.get())
            except ValueError:
                show_message(self.parent, "Error", "Invalid budget limit", "error")
                return
            self.db.add_or_update_budget(
                self.user_id,
                category_var.get().strip(),
                limit_amount,
                int(month_var.get()),
                int(year_var.get()),
            )
            self.set_status("Budget saved", auto_clear=True)
            refresh_budget_table()

        def delete_selected_budget():
            item = budget_tree.selection()
            if not item:
                return
            vals = budget_tree.item(item[0], "values")
            budget_id = vals[0]
            if not budget_id:
                return
            if self.db.delete_budget(int(budget_id), self.user_id):
                self.set_status("Budget deleted", auto_clear=True)
                refresh_budget_table()

        tk.Button(controls, text="Save Budget", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=save_budget).grid(row=0, column=8, padx=8, pady=10)
        tk.Button(controls, text="Refresh", bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=refresh_budget_table).grid(row=0, column=9, padx=4, pady=10)
        tk.Button(controls, text="Delete Selected", bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=delete_selected_budget).grid(row=0, column=10, padx=4, pady=10)
        refresh_budget_table()

        # ---------------- Recurring Bills Tab ----------------
        recurring_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(recurring_tab, text="Recurring Bills")

        recurring_form = tk.Frame(recurring_tab, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        recurring_form.pack(fill=tk.X, pady=(0, 12))
        rb_title = CustomEntry(recurring_form, placeholder="Title")
        rb_category = tk.StringVar()
        rb_amount = CustomEntry(recurring_form, placeholder="Amount")
        rb_freq = tk.StringVar(value="Monthly")
        rb_start = CustomEntry(recurring_form, placeholder="YYYY-MM-DD")
        rb_start.set(str(datetime.now().date()))
        rb_method = tk.StringVar(value="Card")
        rb_desc = CustomEntry(recurring_form, placeholder="Description")

        tk.Label(recurring_form, text="Title", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=0, padx=6, pady=8, sticky=tk.W)
        rb_title.grid(row=0, column=1, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Category", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=2, padx=6, pady=8, sticky=tk.W)
        ttk.Combobox(recurring_form, textvariable=rb_category, values=all_categories, width=14).grid(row=0, column=3, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Amount", bg=COLORS["surface"], font=FONTS["body"]).grid(row=0, column=4, padx=6, pady=8, sticky=tk.W)
        rb_amount.grid(row=0, column=5, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Frequency", bg=COLORS["surface"], font=FONTS["body"]).grid(row=1, column=0, padx=6, pady=8, sticky=tk.W)
        ttk.Combobox(recurring_form, textvariable=rb_freq, values=["Weekly", "Monthly", "Quarterly", "Yearly"], width=12).grid(row=1, column=1, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Start Date", bg=COLORS["surface"], font=FONTS["body"]).grid(row=1, column=2, padx=6, pady=8, sticky=tk.W)
        rb_start.grid(row=1, column=3, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Payment", bg=COLORS["surface"], font=FONTS["body"]).grid(row=1, column=4, padx=6, pady=8, sticky=tk.W)
        ttk.Combobox(recurring_form, textvariable=rb_method, values=["Cash", "Card", "UPI", "Bank", "Other"], width=10).grid(row=1, column=5, padx=6, pady=8, sticky=tk.W)
        tk.Label(recurring_form, text="Description", bg=COLORS["surface"], font=FONTS["body"]).grid(row=2, column=0, padx=6, pady=8, sticky=tk.W)
        rb_desc.grid(row=2, column=1, columnspan=3, padx=6, pady=8, sticky=tk.W)

        recurring_table_frame = tk.Frame(recurring_tab, bg=COLORS["background"])
        recurring_table_frame.pack(fill=tk.BOTH, expand=True)
        rec_cols = ("ID", "Title", "Category", "Amount", "Frequency", "Next Due", "Active")
        recurring_tree = ttk.Treeview(recurring_table_frame, columns=rec_cols, show="headings", height=12)
        for col in rec_cols:
            recurring_tree.heading(col, text=col)
            recurring_tree.column(col, width=110 if col != "Title" else 170)
        self._attach_tree_sorting(recurring_tree, rec_cols)
        rec_scroll = ttk.Scrollbar(recurring_table_frame, orient="vertical", command=recurring_tree.yview)
        recurring_tree.configure(yscroll=rec_scroll.set)
        recurring_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        recurring_btns = tk.Frame(recurring_tab, bg=COLORS["background"])
        recurring_btns.pack(fill=tk.X, pady=(8, 0))

        def refresh_recurring_table():
            recurring_tree.delete(*recurring_tree.get_children())
            rows = self.db.get_recurring_bills(self.user_id)
            for r in rows:
                recurring_tree.insert(
                    "",
                    "end",
                    values=(
                        r["id"],
                        r["title"],
                        r["category"],
                        f"{float(r['amount']):.2f}",
                        r["frequency"],
                        r["next_due_date"],
                        "Yes" if int(r.get("is_active", 1)) else "No",
                    ),
                )

        def add_recurring_bill():
            title = rb_title.get().strip()
            category = rb_category.get().strip()
            start_date = rb_start.get().strip()
            if not title or not category or not start_date:
                show_message(self.parent, "Error", "Title, category, and start date are required", "error")
                return
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                show_message(self.parent, "Error", "Start date must be YYYY-MM-DD", "error")
                return
            try:
                amount = float(rb_amount.get())
            except ValueError:
                show_message(self.parent, "Error", "Invalid recurring amount", "error")
                return
            self.db.add_recurring_bill(
                self.user_id,
                title,
                category,
                amount,
                rb_freq.get().strip() or "Monthly",
                start_date,
                payment_method=rb_method.get().strip(),
                description=rb_desc.get().strip(),
                is_active=1,
            )
            self.set_status("Recurring bill added", auto_clear=True)
            refresh_recurring_table()

        def run_due_bills():
            created = self.db.run_due_recurring_bills(self.user_id)
            self.load_data()
            self.set_status(f"Processed recurring bills: {created}", auto_clear=True)
            show_message(self.parent, "Info", f"Created {created} recurring expense(s)", "info")
            refresh_recurring_table()
            refresh_budget_table()

        def toggle_selected_bill():
            item = recurring_tree.selection()
            if not item:
                return
            vals = recurring_tree.item(item[0], "values")
            bill_id = int(vals[0])
            is_active = 0 if vals[6] == "Yes" else 1
            self.db.update_recurring_bill(bill_id, self.user_id, is_active=is_active)
            refresh_recurring_table()

        def delete_selected_bill():
            item = recurring_tree.selection()
            if not item:
                return
            vals = recurring_tree.item(item[0], "values")
            self.db.delete_recurring_bill(int(vals[0]), self.user_id)
            refresh_recurring_table()

        tk.Button(recurring_form, text="Add Recurring Bill", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=10, pady=6, command=add_recurring_bill).grid(row=2, column=5, padx=6, pady=8)
        tk.Button(recurring_btns, text="Run Due Now", bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=run_due_bills).pack(side=tk.LEFT, padx=4)
        tk.Button(recurring_btns, text="Toggle Active", bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=toggle_selected_bill).pack(side=tk.LEFT, padx=4)
        tk.Button(recurring_btns, text="Delete Selected", bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=delete_selected_bill).pack(side=tk.LEFT, padx=4)
        tk.Button(recurring_btns, text="Refresh", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=refresh_recurring_table).pack(side=tk.LEFT, padx=4)
        refresh_recurring_table()

        # ---------------- Insights Tab ----------------
        insights_tab = tk.Frame(notebook, bg=COLORS["background"])
        notebook.add(insights_tab, text="Insights")

        insights_box = tk.Frame(insights_tab, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        insights_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(insights_box, text="Budget & Recurring Insights", bg=COLORS["surface"], fg=COLORS["primary"], font=FONTS["subheading"]).pack(anchor=tk.W, padx=14, pady=(12, 10))

        alerts = self.feature_manager.get_budget_alerts()
        if not alerts:
            tk.Label(insights_box, text="- No budget alerts right now", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["body"]).pack(anchor=tk.W, padx=18, pady=4)
        else:
            for alert in alerts:
                tk.Label(insights_box, text=f"- {alert}", bg=COLORS["surface"], fg=COLORS["danger"], font=FONTS["body"]).pack(anchor=tk.W, padx=18, pady=4)

        due_count = len([b for b in self.db.get_recurring_bills(self.user_id, active_only=True) if b.get("next_due_date", "") <= datetime.now().strftime("%Y-%m-%d")])
        tk.Label(
            insights_box,
            text=f"- Recurring bills due today or earlier: {due_count}",
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
            font=FONTS["body"]
        ).pack(anchor=tk.W, padx=18, pady=8)

    def _create_highlight_tile(self, parent, title, value, subtitle="", color=None):
        """Reusable card tile for major update pages."""
        tile = tk.Frame(parent, bg=color or COLORS["surface"], relief=tk.FLAT, bd=1)
        tile.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=6)
        tk.Label(tile, text=title, font=FONTS["small"], fg=COLORS["text_secondary"], bg=tile["bg"]).pack(anchor=tk.W, padx=12, pady=(10, 2))
        tk.Label(tile, text=value, font=FONTS["heading"], fg=COLORS["text_primary"], bg=tile["bg"]).pack(anchor=tk.W, padx=12, pady=(0, 2))
        if subtitle:
            tk.Label(tile, text=subtitle, font=FONTS["small"], fg=COLORS["text_secondary"], bg=tile["bg"]).pack(anchor=tk.W, padx=12, pady=(0, 10))
        return tile

    def show_goals_center(self):
        """Major update: Financial goals planner and progress center."""
        self._set_view_state("goals", "Goals Planner", "Target planning, progress tracking, and milestones", "Goals planner loaded")
        self.clear_content()
        create_header(self.content_frame, "Financial Goals Planner", "Set targets, track progress, and close goals faster")

        all_goals = self.db.get_financial_goals(self.user_id)
        active_goals = [g for g in all_goals if g.get("status", "active") == "active"]
        total_target = sum(float(g.get("target_amount", 0) or 0) for g in active_goals)
        total_current = sum(float(g.get("current_amount", 0) or 0) for g in active_goals)
        completion = (total_current / total_target * 100) if total_target > 0 else 0

        top_metrics = tk.Frame(self.content_frame, bg=COLORS["background"])
        top_metrics.pack(fill=tk.X, padx=18, pady=(4, 8))
        self._create_highlight_tile(top_metrics, "Active Goals", str(len(active_goals)), "Currently tracked targets", COLORS["surface"])
        self._create_highlight_tile(top_metrics, "Target Amount", format_currency(total_target), "Combined goal target", COLORS["surface"])
        self._create_highlight_tile(top_metrics, "Saved Progress", format_currency(total_current), "Current saved amount", COLORS["surface"])
        self._create_highlight_tile(top_metrics, "Completion", f"{completion:.1f}%", "Across active goals", COLORS["surface_alt"])

        body = tk.Frame(self.content_frame, bg=COLORS["background"])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        table_card = tk.Frame(body, bg=COLORS["surface"])
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        cols = ("id", "title", "target", "current", "progress", "due_date", "category", "status")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=18)
        for col, text, width in [
            ("id", "ID", 50),
            ("title", "Goal", 180),
            ("target", "Target", 100),
            ("current", "Saved", 100),
            ("progress", "Progress %", 95),
            ("due_date", "Due Date", 110),
            ("category", "Category", 100),
            ("status", "Status", 85),
        ]:
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor=tk.W)
        self._attach_tree_sorting(tree, cols)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tree_scroll = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        form_card = tk.Frame(body, bg=COLORS["surface"])
        form_card.grid(row=0, column=1, sticky="nsew")
        tk.Label(form_card, text="Goal Form", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["primary"]).pack(anchor=tk.W, padx=12, pady=(12, 8))

        form = tk.Frame(form_card, bg=COLORS["surface"])
        form.pack(fill=tk.X, padx=12, pady=(0, 8))
        form.grid_columnconfigure(1, weight=1)

        goal_id_var = tk.StringVar()
        title_var = tk.StringVar()
        target_var = tk.StringVar()
        saved_var = tk.StringVar(value="0")
        due_var = tk.StringVar()
        category_var = tk.StringVar(value="General")
        status_var = tk.StringVar(value="active")
        notes_var = tk.StringVar()

        field_rows = [
            ("Goal ID", goal_id_var, True),
            ("Title", title_var, False),
            ("Target Amount", target_var, False),
            ("Current Saved", saved_var, False),
            ("Due Date (YYYY-MM-DD)", due_var, False),
            ("Category", category_var, False),
            ("Status (active/completed)", status_var, False),
            ("Notes", notes_var, False),
        ]
        entries = {}
        for i, (label, var, readonly) in enumerate(field_rows):
            tk.Label(form, text=label, font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["text_secondary"]).grid(row=i, column=0, sticky=tk.W, pady=(0, 4))
            entry = ttk.Entry(form, textvariable=var)
            if readonly:
                entry.configure(state="readonly")
            entry.grid(row=i, column=1, sticky=tk.EW, pady=(0, 8))
            entries[label] = entry

        def clear_form():
            entries["Goal ID"].configure(state="normal")
            goal_id_var.set("")
            entries["Goal ID"].configure(state="readonly")
            title_var.set("")
            target_var.set("")
            saved_var.set("0")
            due_var.set("")
            category_var.set("General")
            status_var.set("active")
            notes_var.set("")

        def refresh_table():
            tree.delete(*tree.get_children())
            for g in self.db.get_financial_goals(self.user_id):
                target = float(g.get("target_amount", 0) or 0)
                current = float(g.get("current_amount", 0) or 0)
                percent = (current / target * 100) if target > 0 else 0
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        g["id"], g.get("title", ""), f"{target:.2f}", f"{current:.2f}",
                        f"{percent:.1f}", g.get("due_date", "") or "", g.get("category", ""),
                        g.get("status", "active")
                    )
                )

        def load_selected(event=None):
            selected = tree.selection()
            if not selected:
                return
            vals = tree.item(selected[0], "values")
            entries["Goal ID"].configure(state="normal")
            goal_id_var.set(vals[0])
            entries["Goal ID"].configure(state="readonly")
            title_var.set(vals[1])
            target_var.set(vals[2])
            saved_var.set(vals[3])
            due_var.set(vals[5])
            category_var.set(vals[6] or "General")
            status_var.set(vals[7] or "active")

        tree.bind("<<TreeviewSelect>>", load_selected)

        def save_goal():
            title = title_var.get().strip()
            if not title:
                show_message(self.parent, "Error", "Goal title is required", "error")
                return
            try:
                target_amount = float(target_var.get())
                current_amount = float(saved_var.get() or 0)
            except ValueError:
                show_message(self.parent, "Error", "Target/current amount must be numeric", "error")
                return
            due_date = due_var.get().strip()
            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    show_message(self.parent, "Error", "Due date format must be YYYY-MM-DD", "error")
                    return

            goal_id = goal_id_var.get().strip()
            if goal_id:
                self.db.update_financial_goal(
                    int(goal_id),
                    self.user_id,
                    title=title,
                    target_amount=target_amount,
                    current_amount=current_amount,
                    due_date=due_date or None,
                    category=category_var.get().strip() or "General",
                    status=(status_var.get().strip().lower() or "active"),
                    notes=notes_var.get().strip(),
                )
                self.set_status("Goal updated", auto_clear=True)
            else:
                self.db.add_financial_goal(
                    self.user_id,
                    title,
                    target_amount,
                    due_date=due_date,
                    category=category_var.get().strip() or "General",
                    notes=notes_var.get().strip(),
                )
                self.set_status("Goal created", auto_clear=True)

            clear_form()
            refresh_table()

        def add_progress():
            goal_id = goal_id_var.get().strip()
            if not goal_id:
                show_message(self.parent, "Error", "Select a goal first", "error")
                return
            try:
                inc = float(simpledialog.askstring("Add Progress", "Amount to add:", parent=self.parent) or "0")
            except ValueError:
                show_message(self.parent, "Error", "Invalid amount", "error")
                return
            goals = {g["id"]: g for g in self.db.get_financial_goals(self.user_id)}
            row = goals.get(int(goal_id))
            if not row:
                return
            new_amt = float(row.get("current_amount", 0) or 0) + inc
            status = "completed" if new_amt >= float(row.get("target_amount", 0) or 0) else row.get("status", "active")
            self.db.update_financial_goal(int(goal_id), self.user_id, current_amount=new_amt, status=status)
            saved_var.set(f"{new_amt:.2f}")
            status_var.set(status)
            refresh_table()
            self.set_status("Goal progress updated", auto_clear=True)

        def delete_goal():
            goal_id = goal_id_var.get().strip()
            if not goal_id:
                show_message(self.parent, "Error", "Select a goal first", "error")
                return
            if not messagebox.askyesno("Delete Goal", "Delete selected goal?"):
                return
            self.db.delete_financial_goal(int(goal_id), self.user_id)
            clear_form()
            refresh_table()
            self.set_status("Goal deleted", auto_clear=True)

        actions = tk.Frame(form_card, bg=COLORS["surface"])
        actions.pack(fill=tk.X, padx=12, pady=(4, 12))
        tk.Button(actions, text="Save Goal", command=save_goal, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Add Progress", command=add_progress, bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Delete Goal", command=delete_goal, bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Clear", command=clear_form, bg=COLORS["surface_alt"], fg=COLORS["text_primary"], relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)

        refresh_table()

    def show_insights_center(self):
        """Major update: dedicated insights center with account scope."""
        self._set_view_state("insights", "Insights Center", "Actionable account-wise intelligence and trends", "Insights center loaded")
        self.clear_content()
        create_header(self.content_frame, "Smart Insights Center", "Advanced trends, anomalies, and action-ready recommendations")

        accounts = self.db.get_managed_accounts(self.user_id)
        scope_map = {"All Accounts": "ALL", "Personal (Main)": None}
        for acc in accounts:
            scope_map[acc["account_name"]] = acc["id"]
        if self.insights_account_scope not in scope_map.values():
            self.insights_account_scope = "ALL"

        scope_label_map = {v: k for k, v in scope_map.items()}
        scope_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        scope_frame.pack(fill=tk.X, padx=18, pady=(0, 8))
        tk.Label(scope_frame, text="Insights Scope:", font=FONTS["body"], fg=COLORS["text_primary"], bg=COLORS["background"]).pack(side=tk.LEFT, padx=(0, 8))
        scope_var = tk.StringVar(value=scope_label_map.get(self.insights_account_scope, "All Accounts"))
        scope_combo = ttk.Combobox(scope_frame, textvariable=scope_var, values=list(scope_map.keys()), width=28, state="readonly")
        scope_combo.pack(side=tk.LEFT)

        def apply_scope(event=None):
            self.insights_account_scope = scope_map.get(scope_var.get(), "ALL")
            self.show_insights_center()

        scope_combo.bind("<<ComboboxSelected>>", apply_scope)

        all_expenses = self.db.get_expenses(self.user_id)
        all_income = self.db.get_income(self.user_id)
        expenses = self._filter_rows_by_account_scope(all_expenses, self.insights_account_scope)
        income = self._filter_rows_by_account_scope(all_income, self.insights_account_scope)

        total_income = sum(float(i.get("amount", 0) or 0) for i in income)
        total_expense = sum(float(e.get("amount", 0) or 0) for e in expenses)
        balance = total_income - total_expense
        savings_rate = ((balance / total_income) * 100) if total_income > 0 else 0
        ratio = (total_expense / total_income) if total_income > 0 else 0

        health_score = 100.0
        if ratio > 1:
            health_score -= 40
        elif ratio > 0.85:
            health_score -= 20
        if savings_rate < 0:
            health_score -= 35
        elif savings_rate < 10:
            health_score -= 20
        elif savings_rate < 20:
            health_score -= 10
        if total_expense == 0 and total_income == 0:
            health_score = 0
        health_score = max(0, min(100, health_score))

        top = tk.Frame(self.content_frame, bg=COLORS["background"])
        top.pack(fill=tk.X, padx=18, pady=(4, 8))
        self._create_highlight_tile(top, "Health Score", f"{health_score:.0f}/100", "Financial stability metric", COLORS["surface_alt"])
        self._create_highlight_tile(top, "Savings Rate", f"{savings_rate:.1f}%", "Income preserved after expenses", COLORS["surface"])
        self._create_highlight_tile(top, "Expense/Income", f"{ratio:.2f}", "Lower is healthier", COLORS["surface"])
        self._create_highlight_tile(top, "Net Balance", format_currency(balance), "Current financial position", COLORS["surface"])

        body = tk.Frame(self.content_frame, bg=COLORS["background"])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        recommendations_card = tk.Frame(body, bg=COLORS["surface"])
        recommendations_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        tk.Label(recommendations_card, text="Recommendations", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["primary"]).pack(anchor=tk.W, padx=12, pady=(12, 8))

        recommendations = []
        if ratio > 0.85:
            recommendations.append("Expense ratio is high. Try reducing discretionary spending by 10-15%.")
        if savings_rate < 15:
            recommendations.append("Savings rate is below 15%. Set one fixed monthly auto-transfer goal.")
        if balance < 0:
            recommendations.append("Balance is negative. Prioritize paying essential expenses first this month.")

        cat_totals = {}
        for row in expenses:
            cat = row.get("category", "Other")
            cat_totals[cat] = cat_totals.get(cat, 0) + float(row.get("amount", 0) or 0)
        top_cats = sorted(cat_totals.items(), key=lambda kv: kv[1], reverse=True)[:3]
        if top_cats:
            names = ", ".join(c[0] for c in top_cats)
            recommendations.append(f"Top spend categories: {names}. Review these for optimization.")
        if not recommendations:
            recommendations.append("Performance is stable. Keep current budgeting pattern and goal contributions.")

        for rec in recommendations:
            tk.Label(recommendations_card, text=f"- {rec}", font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"], wraplength=520, justify=tk.LEFT).pack(anchor=tk.W, padx=14, pady=3)

        anomaly_card = tk.Frame(body, bg=COLORS["surface"])
        anomaly_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        tk.Label(anomaly_card, text="Large Transaction Alerts", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["danger"]).pack(anchor=tk.W, padx=12, pady=(12, 8))
        largest = sorted(expenses, key=lambda r: float(r.get("amount", 0) or 0), reverse=True)[:5]
        if not largest:
            tk.Label(anomaly_card, text="- No transactions yet", font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(anchor=tk.W, padx=14, pady=4)
        else:
            for row in largest:
                tk.Label(
                    anomaly_card,
                    text=f"- {row.get('date', '')} | {row.get('category', '')} | {format_currency(float(row.get('amount', 0) or 0))}",
                    font=FONTS["body"], bg=COLORS["surface"], fg=COLORS["text_primary"]
                ).pack(anchor=tk.W, padx=14, pady=2)

        trend_card = tk.Frame(body, bg=COLORS["surface"])
        trend_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
        tk.Label(trend_card, text="Monthly Spending Trend (Last 12 Months)", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["primary"]).pack(anchor=tk.W, padx=12, pady=(12, 8))

        trend_cols = ("month", "total")
        trend_tree = ttk.Treeview(trend_card, columns=trend_cols, show="headings", height=12)
        trend_tree.heading("month", text="Month")
        trend_tree.heading("total", text="Total Spent")
        trend_tree.column("month", width=180, anchor=tk.W)
        trend_tree.column("total", width=180, anchor=tk.W)
        trend_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=(0, 12))
        trend_scroll = ttk.Scrollbar(trend_card, orient="vertical", command=trend_tree.yview)
        trend_tree.configure(yscrollcommand=trend_scroll.set)
        trend_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=(0, 12))

        trend_map = {}
        for row in expenses:
            date_value = str(row.get("date", "") or "")
            month_key = date_value[:7] if len(date_value) >= 7 else "Unknown"
            trend_map[month_key] = trend_map.get(month_key, 0) + float(row.get("amount", 0) or 0)
        for month in sorted(trend_map.keys(), reverse=True)[:12]:
            trend_tree.insert("", tk.END, values=(month, format_currency(trend_map[month])))

    def show_notification_center(self):
        """Major update: notification center for alerts and reminders."""
        self._set_view_state("notifications", "Notification Center", "Smart alerts, reminders, and risk signals", "Notification center loaded")
        self.clear_content()
        create_header(self.content_frame, "Notification Center", "Budget alerts, recurring reminders, and system warnings")

        top = tk.Frame(self.content_frame, bg=COLORS["background"])
        top.pack(fill=tk.X, padx=18, pady=(2, 8))
        unread_only_var = tk.BooleanVar(value=False)

        tk.Button(
            top, text="Generate Smart Alerts", bg=COLORS["primary"], fg="white",
            relief=tk.FLAT, padx=12, pady=6,
            command=lambda: [self.db.generate_system_notifications(self.user_id), refresh_notifications(), self.set_status("Smart alerts generated", auto_clear=True)]
        ).pack(side=tk.LEFT, padx=4)
        tk.Checkbutton(
            top, text="Unread Only", variable=unread_only_var, bg=COLORS["background"],
            fg=COLORS["text_primary"], command=lambda: refresh_notifications()
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            top, text="Clear All", bg=COLORS["danger"], fg="white", relief=tk.FLAT,
            padx=12, pady=6,
            command=lambda: [self.db.clear_notifications(self.user_id), refresh_notifications(), self.set_status("All notifications cleared", auto_clear=True)]
        ).pack(side=tk.RIGHT, padx=4)

        table_card = tk.Frame(self.content_frame, bg=COLORS["surface"])
        table_card.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        cols = ("id", "title", "message", "severity", "status", "created_at")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=20)
        for col, label, width in [
            ("id", "ID", 55),
            ("title", "Title", 170),
            ("message", "Message", 500),
            ("severity", "Severity", 95),
            ("status", "Read", 70),
            ("created_at", "Created", 150),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor=tk.W)
        self._attach_tree_sorting(tree, cols)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scroll = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        def refresh_notifications():
            tree.delete(*tree.get_children())
            rows = self.db.get_notifications(self.user_id, unread_only=unread_only_var.get())
            for n in rows:
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        n["id"],
                        n.get("title", ""),
                        n.get("message", ""),
                        n.get("severity", "info"),
                        "Yes" if int(n.get("is_read", 0)) else "No",
                        n.get("created_at", ""),
                    ),
                )

        def mark_read(read=True):
            selected = tree.selection()
            if not selected:
                return
            for item in selected:
                vals = tree.item(item, "values")
                self.db.mark_notification_read(int(vals[0]), self.user_id, is_read=read)
            refresh_notifications()
            self.set_status("Notification state updated", auto_clear=True)

        def delete_selected():
            selected = tree.selection()
            if not selected:
                return
            for item in selected:
                vals = tree.item(item, "values")
                self.db.delete_notification(int(vals[0]), self.user_id)
            refresh_notifications()
            self.set_status("Selected notifications deleted", auto_clear=True)

        controls = tk.Frame(self.content_frame, bg=COLORS["background"])
        controls.pack(fill=tk.X, padx=18, pady=(0, 14))
        tk.Button(controls, text="Mark Read", bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=lambda: mark_read(True)).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Mark Unread", bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=lambda: mark_read(False)).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Delete Selected", bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=delete_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Refresh", bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6, command=refresh_notifications).pack(side=tk.LEFT, padx=4)

        refresh_notifications()

    def show_notes_hub(self):
        """Insane update: full notes workspace."""
        self._set_view_state("notes", "Notes Hub", "Capture and organize accounting notes quickly", "Notes hub loaded")
        self.clear_content()
        create_header(self.content_frame, "Notes Hub", "Capture ideas, decisions, and quick bookkeeping notes")

        top = tk.Frame(self.content_frame, bg=COLORS["background"])
        top.pack(fill=tk.X, padx=18, pady=(4, 10))
        self._create_highlight_tile(top, "Total Notes", str(len(self.db.get_quick_notes(self.user_id))), "Personal workspace notes", COLORS["surface"])

        body = tk.Frame(self.content_frame, bg=COLORS["background"])
        body.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=COLORS["surface"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = tk.Frame(body, bg=COLORS["surface"])
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(left, text="Notes", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["primary"]).pack(anchor=tk.W, padx=12, pady=(12, 8))
        listbox = tk.Listbox(left, font=FONTS["body"], bg=COLORS["surface_alt"], fg=COLORS["text_primary"], relief=tk.FLAT)
        listbox.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

        note_id_var = tk.StringVar()
        title_var = tk.StringVar()
        color_var = tk.StringVar(value="blue")
        pin_var = tk.BooleanVar(value=False)

        tk.Label(right, text="Title", font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(anchor=tk.W, padx=12, pady=(12, 4))
        ttk.Entry(right, textvariable=title_var).pack(fill=tk.X, padx=12, pady=(0, 8), ipady=5)
        tk.Label(right, text="Body", font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(anchor=tk.W, padx=12, pady=(0, 4))
        body_text = tk.Text(right, height=14, font=FONTS["body"], bg=COLORS["surface_alt"], fg=COLORS["text_primary"], relief=tk.FLAT)
        body_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        controls = tk.Frame(right, bg=COLORS["surface"])
        controls.pack(fill=tk.X, padx=12, pady=(0, 8))
        ttk.Combobox(controls, textvariable=color_var, values=["blue", "green", "orange", "red", "purple"], width=12, state="readonly").pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(controls, text="Pinned", variable=pin_var, bg=COLORS["surface"], fg=COLORS["text_primary"], selectcolor=COLORS["surface"]).pack(side=tk.LEFT)

        notes_cache = {}

        def refresh_notes():
            nonlocal notes_cache
            notes_cache = {n["id"]: n for n in self.db.get_quick_notes(self.user_id)}
            listbox.delete(0, tk.END)
            for n in notes_cache.values():
                prefix = "[PIN] " if int(n.get("is_pinned", 0)) else ""
                listbox.insert(tk.END, f"{prefix}{n['id']}: {n.get('title', '')}")

        def clear_form():
            note_id_var.set("")
            title_var.set("")
            color_var.set("blue")
            pin_var.set(False)
            body_text.delete("1.0", tk.END)

        def load_selected(event=None):
            if not listbox.curselection():
                return
            raw = listbox.get(listbox.curselection()[0])
            note_id = int(raw.split(":")[0].replace("[PIN]", "").strip())
            row = notes_cache.get(note_id)
            if not row:
                return
            note_id_var.set(str(note_id))
            title_var.set(row.get("title", ""))
            color_var.set(row.get("color_tag", "blue"))
            pin_var.set(bool(int(row.get("is_pinned", 0))))
            body_text.delete("1.0", tk.END)
            body_text.insert("1.0", row.get("body", ""))

        def save_note():
            title = title_var.get().strip()
            if not title:
                show_message(self.parent, "Error", "Title is required", "error")
                return
            payload = {
                "title": title,
                "body": body_text.get("1.0", tk.END).strip(),
                "color_tag": color_var.get(),
                "is_pinned": 1 if pin_var.get() else 0,
            }
            if note_id_var.get().strip():
                self.db.update_quick_note(int(note_id_var.get()), self.user_id, **payload)
                self.set_status("Note updated", auto_clear=True)
            else:
                self.db.add_quick_note(self.user_id, **payload)
                self.set_status("Note created", auto_clear=True)
            refresh_notes()
            clear_form()

        def delete_note():
            if not note_id_var.get().strip():
                show_message(self.parent, "Error", "Select a note first", "error")
                return
            self.db.delete_quick_note(int(note_id_var.get()), self.user_id)
            refresh_notes()
            clear_form()
            self.set_status("Note deleted", auto_clear=True)

        actions = tk.Frame(right, bg=COLORS["surface"])
        actions.pack(fill=tk.X, padx=12, pady=(0, 12))
        tk.Button(actions, text="Save Note", command=save_note, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="Delete", command=delete_note, bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(actions, text="New", command=clear_form, bg=COLORS["surface_alt"], fg=COLORS["text_primary"], relief=tk.FLAT, padx=10, pady=6).pack(side=tk.LEFT, padx=4)
        listbox.bind("<<ListboxSelect>>", load_selected)

        refresh_notes()

    def show_reminders_hub(self):
        """Insane update: reminders planner with due tracking."""
        self._set_view_state("reminders", "Reminders", "Due-date planner for operational and financial tasks", "Reminders loaded")
        self.clear_content()
        create_header(self.content_frame, "Reminders Planner", "Track deadlines and daily action items")

        controls = tk.Frame(self.content_frame, bg=COLORS["background"])
        controls.pack(fill=tk.X, padx=18, pady=(4, 8))
        title_var = tk.StringVar()
        due_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        priority_var = tk.StringVar(value="medium")
        note_var = tk.StringVar()
        pending_only_var = tk.BooleanVar(value=False)

        ttk.Entry(controls, textvariable=title_var, width=28).pack(side=tk.LEFT, padx=4)
        ttk.Entry(controls, textvariable=due_var, width=14).pack(side=tk.LEFT, padx=4)
        ttk.Combobox(controls, textvariable=priority_var, values=["low", "medium", "high"], state="readonly", width=10).pack(side=tk.LEFT, padx=4)
        ttk.Entry(controls, textvariable=note_var, width=28).pack(side=tk.LEFT, padx=4)
        tk.Checkbutton(controls, text="Pending Only", variable=pending_only_var, bg=COLORS["background"], fg=COLORS["text_primary"]).pack(side=tk.LEFT, padx=8)

        table_card = tk.Frame(self.content_frame, bg=COLORS["surface"])
        table_card.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        cols = ("id", "title", "due_date", "priority", "note", "done")
        tree = ttk.Treeview(table_card, columns=cols, show="headings", height=18)
        for col, w in [("id", 55), ("title", 190), ("due_date", 120), ("priority", 90), ("note", 420), ("done", 80)]:
            tree.heading(col, text=col.replace("_", " ").title())
            tree.column(col, width=w, anchor=tk.W)
        self._attach_tree_sorting(tree, cols)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        sc = ttk.Scrollbar(table_card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sc.set)
        sc.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)

        def refresh():
            tree.delete(*tree.get_children())
            for r in self.db.get_reminders(self.user_id, pending_only=pending_only_var.get()):
                tree.insert("", tk.END, values=(r["id"], r["title"], r["due_date"], r.get("priority", "medium"), r.get("note", ""), "Yes" if int(r.get("is_done", 0)) else "No"))

        def add():
            title = title_var.get().strip()
            due = due_var.get().strip()
            if not title or not due:
                show_message(self.parent, "Error", "Title and due date are required", "error")
                return
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                show_message(self.parent, "Error", "Due date format must be YYYY-MM-DD", "error")
                return
            self.db.add_reminder(self.user_id, title, due, priority_var.get(), note_var.get().strip())
            title_var.set("")
            note_var.set("")
            refresh()
            self.set_status("Reminder added", auto_clear=True)

        def toggle_done():
            if not tree.selection():
                return
            vals = tree.item(tree.selection()[0], "values")
            reminder_id = int(vals[0])
            done = vals[5] == "Yes"
            self.db.update_reminder(reminder_id, self.user_id, is_done=0 if done else 1)
            refresh()
            self.set_status("Reminder status updated", auto_clear=True)

        def delete():
            if not tree.selection():
                return
            vals = tree.item(tree.selection()[0], "values")
            self.db.delete_reminder(int(vals[0]), self.user_id)
            refresh()
            self.set_status("Reminder deleted", auto_clear=True)

        btns = tk.Frame(self.content_frame, bg=COLORS["background"])
        btns.pack(fill=tk.X, padx=18, pady=(0, 12))
        tk.Button(btns, text="Add Reminder", command=add, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Toggle Done", command=toggle_done, bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Delete", command=delete, bg=COLORS["danger"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Refresh", command=refresh, bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=6).pack(side=tk.LEFT, padx=4)
        pending_only_var.trace_add("write", lambda *args: refresh())
        refresh()

    def show_data_quality_center(self):
        """Insane update: data quality diagnostics and cleanup shortcuts."""
        self._set_view_state("data_quality", "Data Quality", "Data diagnostics, cleanup insights, and duplicate checks", "Data quality center loaded")
        self.clear_content()
        create_header(self.content_frame, "Data Quality Center", "Find missing details, uncategorized rows, and duplicate risks")

        report = self.db.get_data_quality_report(self.user_id)
        cards = tk.Frame(self.content_frame, bg=COLORS["background"])
        cards.pack(fill=tk.X, padx=18, pady=(4, 8))
        self._create_highlight_tile(cards, "Missing Expense Desc", str(report["missing_expense_descriptions"]), "Expenses without description", COLORS["surface"])
        self._create_highlight_tile(cards, "Missing Income Desc", str(report["missing_income_descriptions"]), "Income without description", COLORS["surface"])
        self._create_highlight_tile(cards, "Uncategorized Expenses", str(report["uncategorized_expenses"]), "Category empty or Other", COLORS["surface"])
        self._create_highlight_tile(cards, "Possible Duplicates", str(report["possible_duplicates"]), "Duplicate transaction signals", COLORS["surface_alt"])

        panel = tk.Frame(self.content_frame, bg=COLORS["surface"])
        panel.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        tk.Label(panel, text="Cleanup Actions", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["primary"]).pack(anchor=tk.W, padx=12, pady=(12, 8))
        tk.Label(panel, text="- Use Transactions > double-click to edit missing details quickly.", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(anchor=tk.W, padx=14, pady=3)
        tk.Label(panel, text="- Use Insights Center to identify top categories and reclassify recurring spend.", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(anchor=tk.W, padx=14, pady=3)
        tk.Label(panel, text="- Use Scenario Lab to test budget adjustments before applying real changes.", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONTS["body"]).pack(anchor=tk.W, padx=14, pady=3)
        tk.Button(panel, text="Open Transactions", command=self.show_transactions, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(anchor=tk.W, padx=14, pady=(12, 0))

    def show_scenario_lab(self):
        """Insane update: what-if simulation for monthly finance planning."""
        self._set_view_state("scenario", "Scenario Lab", "What-if simulations before financial decisions", "Scenario lab loaded")
        self.clear_content()
        create_header(self.content_frame, "Scenario Lab", "Run what-if simulations before taking financial decisions")

        summary = self.db.get_summary(self.user_id)
        base_income = float(summary.get("total_income", 0) or 0)
        base_expense = float(summary.get("total_expenses", 0) or 0)
        base_balance = base_income - base_expense

        top = tk.Frame(self.content_frame, bg=COLORS["background"])
        top.pack(fill=tk.X, padx=18, pady=(2, 8))
        self._create_highlight_tile(top, "Current Income", format_currency(base_income), "Baseline", COLORS["surface"])
        self._create_highlight_tile(top, "Current Expense", format_currency(base_expense), "Baseline", COLORS["surface"])
        self._create_highlight_tile(top, "Current Balance", format_currency(base_balance), "Baseline", COLORS["surface_alt"])

        card = tk.Frame(self.content_frame, bg=COLORS["surface"])
        card.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        form = tk.Frame(card, bg=COLORS["surface"])
        form.pack(fill=tk.X, padx=14, pady=14)
        form.grid_columnconfigure(1, weight=1)

        income_change_var = tk.StringVar(value="0")
        expense_change_var = tk.StringVar(value="0")
        one_time_expense_var = tk.StringVar(value="0")
        month_var = tk.StringVar(value=datetime.now().strftime("%Y-%m"))

        tk.Label(form, text="Income Change %", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["small"]).grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Entry(form, textvariable=income_change_var).grid(row=0, column=1, sticky=tk.EW, pady=4)
        tk.Label(form, text="Expense Change %", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["small"]).grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Entry(form, textvariable=expense_change_var).grid(row=1, column=1, sticky=tk.EW, pady=4)
        tk.Label(form, text="One-time Extra Expense", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["small"]).grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Entry(form, textvariable=one_time_expense_var).grid(row=2, column=1, sticky=tk.EW, pady=4)
        tk.Label(form, text="Scenario Month", bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONTS["small"]).grid(row=3, column=0, sticky=tk.W, pady=4)
        ttk.Entry(form, textvariable=month_var).grid(row=3, column=1, sticky=tk.EW, pady=4)

        result_box = tk.Text(card, height=12, font=FONTS["body"], bg=COLORS["surface_alt"], fg=COLORS["text_primary"], relief=tk.FLAT)
        result_box.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 12))

        def run_simulation():
            try:
                income_pct = float(income_change_var.get())
                expense_pct = float(expense_change_var.get())
                one_time = float(one_time_expense_var.get())
            except ValueError:
                show_message(self.parent, "Error", "Scenario values must be numeric", "error")
                return
            sim_income = base_income * (1 + income_pct / 100.0)
            sim_expense = base_expense * (1 + expense_pct / 100.0) + one_time
            sim_balance = sim_income - sim_expense
            runway = (sim_income / sim_expense) if sim_expense > 0 else 0
            result_box.delete("1.0", tk.END)
            result_box.insert(
                tk.END,
                f"Scenario Month: {month_var.get().strip()}\n\n"
                f"Simulated Income: {format_currency(sim_income)}\n"
                f"Simulated Expense: {format_currency(sim_expense)}\n"
                f"Projected Balance: {format_currency(sim_balance)}\n"
                f"Income/Expense Multiplier: {runway:.2f}\n\n"
            )
            if sim_balance < 0:
                result_box.insert(tk.END, "Risk: Balance turns negative. Consider reducing expense growth or increasing income.\n")
            elif sim_balance < base_balance:
                result_box.insert(tk.END, "Warning: Balance is lower than baseline.\n")
            else:
                result_box.insert(tk.END, "Good: Scenario improves or maintains baseline balance.\n")
            self.set_status("Scenario simulation completed", auto_clear=True)

        btns = tk.Frame(card, bg=COLORS["surface"])
        btns.pack(fill=tk.X, padx=14, pady=(0, 12))
        tk.Button(btns, text="Run Simulation", command=run_simulation, bg=COLORS["primary"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Open Budget", command=self.show_budget, bg=COLORS["secondary"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Open Goals", command=self.show_goals_center, bg=COLORS["accent"], fg="white", relief=tk.FLAT, padx=12, pady=7).pack(side=tk.LEFT, padx=4)

    def show_profile(self):
        """Show user profile"""
        self._set_view_state("profile", "Profile", "Account owner details and preferences", "Profile loaded")
        self.clear_content()
        create_header(self.content_frame, "Profile", "Manage your account information")
        
        profile_frame = tk.Frame(self.content_frame, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Profile info
        info_grid = tk.Frame(profile_frame, bg=COLORS["surface"])
        info_grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        fields = [
            ("Full Name", "full_name"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Address", "address"),
            ("City", "city"),
            ("State", "state"),
            ("ZIP Code", "zip_code"),
        ]
        
        entries = {}
        row = 0
        for label, field in fields:
            tk.Label(
                info_grid,
                text=label,
                font=FONTS["body"],
                fg=COLORS["text_primary"],
                bg=COLORS["surface"]
            ).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
            
            entry = CustomEntry(info_grid)
            entry.grid(row=row, column=1, sticky=tk.EW, padx=10, pady=5)
            entry.set(str(self.user_data.get(field, "")))
            entries[field] = entry
            
            row += 1
        
        info_grid.columnconfigure(1, weight=1)
        
        # Save button
        def save_profile():
            update_data = {field: entries[field].get() for _, field in fields}
            self.db.update_user(self.user_id, **update_data)
            # Refresh user data
            user_info = self.db.get_user(self.user_id)
            if user_info:
                self.user_data = user_info
            show_message(self.parent, "Success", "Profile updated successfully", "info")
            self.set_status("Profile updated successfully", auto_clear=True)
            self.show_profile()  # Refresh the profile display
        
        save_btn = tk.Button(
            info_grid,
            text="Save Changes",
            command=save_profile,
            font=FONTS["body"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        save_btn.grid(row=row, column=1, sticky=tk.E, padx=10, pady=20)

    def logout(self):
        """Logout user"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.parent.destroy()

    def show_features(self):
        """Show all available features"""
        self._set_view_state("features", "Features & Capabilities", "Complete feature inventory and release highlights", "Features loaded")
        self.clear_content()
        
        create_header(self.content_frame, "OG CA", "Major Update - Advanced Control Account Suite")
        
        # Scrollable features list  
        canvas = tk.Canvas(self.content_frame, bg=COLORS["background"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["background"])
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Feature categories
        categories = {
            "OG CA Major Update - 50 New Features": [
                "Live design preset engine (Ocean/Graphite/Emerald/Sunset)",
                "Real-time runtime theme switching from top bar",
                "Power command palette (Ctrl+K)",
                "Sidebar menu search",
                "Scrollable sidebar menu with mouse wheel",
                "Notes Hub with pinned notes and color tags",
                "Reminders planner with due-date tracking",
                "Data Quality Center diagnostics",
                "Scenario Lab what-if simulator",
                "Dashboard workspace quick-launch strip",
                "Account-scoped insights selector",
                "Financial goals planner module",
                "Goal progress tracking and milestone updates",
                "Goal completion status automation",
                "Dedicated insights center page",
                "Large transaction anomaly highlights",
                "Monthly spending trend insights table",
                "Dedicated notification center page",
                "Smart alert generation (budget, due bills, negative balance)",
                "Notification read/unread state management",
                "Notification bulk clear and selective delete",
                "Welcome popup after login",
                "Top bar welcome username",
                "Session status bar with timestamps",
                "Quick add expense button",
                "Quick add income button",
                "Keyboard shortcut navigation",
                "F5 page refresh shortcut",
                "Global quick action flow",
                "Sortable expense columns",
                "Sortable income columns",
                "Live expense search",
                "Live income search",
                "Expense list live totals",
                "Income list live totals",
                "Transaction edit shortcut (double-click)",
                "Email setup help dialog",
                "SMTP configuration wizard",
                "Reusable SMTP settings",
                "Test email sender",
                "Safer email report attachment flow",
                "Automatic temp file cleanup for email reports",
                "Data & Email tools panel in Reports",
                "Export all data (CSV)",
                "JSON full backup export",
                "JSON backup import",
                "SQLite DB direct backup",
                "SQLite DB restore",
                "Command Center launcher",
                "Quick calculator utility",
                "Monthly snapshot text export",
                "Keyboard shortcuts help dialog",
                "Improved report card actions",
                "Session-based feedback messages",
                "Profile update status feedback",
                "Accounts page status feedback",
                "Reports page status feedback",
                "Budget page status feedback",
                "Features page status feedback",
                "Dashboard page status feedback",
                "Transactions page status feedback",
                "Improved table visual styling",
                "Improved notebook tab styling",
                "Cleaner feature labels (encoding-safe)",
                "Cleaner currency display labels",
                "Cleaner account card email display",
                "Refined top navigation spacing",
                "Refined sidebar branding and labels",
                "OG CA app renaming",
                "Auth screen brand overhaul",
                "Reduced encoding-related UI noise"
            ],
            "Core Features": [
                "Track expenses and income",
                "Manage multiple accounts",
                "Budget planning and alerts",
                "Category-wise analysis",
                "Quick add income/expense actions",
                "Keyboard navigation shortcuts"
            ],
            "Analytics & Reports": [
                "Financial health scoring",
                "Spending trends analysis",
                "Category breakdown views",
                "Monthly/Quarterly/Annual reports",
                "Email PDF exports"
            ],
            "Security & Data": [
                "Secure authentication",
                "Password hashing (PBKDF2)",
                "Auto-save transactions",
                "Data persistence",
                "Database backup and restore"
            ]
        }
        
        for category_title, features in categories.items():
            cat_frame = tk.Frame(scrollable_frame, bg=COLORS["surface"], relief=tk.RIDGE, bd=2)
            cat_frame.pack(fill=tk.X, padx=20, pady=15)
            
            tk.Label(cat_frame, text=category_title, font=FONTS["subheading"],
                    fg=COLORS["primary"], bg=COLORS["surface"]).pack(anchor=tk.W, padx=15, pady=(15, 10))
            
            for feature in features:
                feat_frame = tk.Frame(cat_frame, bg=COLORS["background"])
                feat_frame.pack(fill=tk.X, padx=15, pady=5)
                tk.Label(feat_frame, text=f"- {feature}", font=FONTS["body"],
                        fg=COLORS["accent"], bg=COLORS["background"]).pack(anchor=tk.W, padx=10)
            
            tk.Frame(cat_frame, bg=COLORS["surface"]).pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        scrollbar.pack(side="right", fill="y")






