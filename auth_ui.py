"""Authentication UI Module - complete redesigned login/register experience."""
import tkinter as tk
from tkinter import ttk

from config import COLORS, FONTS
from utils import validate_email, validate_password, show_message
from database import Database


class AuthenticationUI:
    def __init__(self, parent, on_login_success):
        self.parent = parent
        self.on_login_success = on_login_success
        self.db = Database()

        self.current_mode = "login"
        self._auth_compact = False
        self.root_container = None
        self.hero_panel = None
        self.form_panel = None
        self.login_frame = None
        self.register_frame = None

        self.login_username = tk.StringVar()
        self.login_password = tk.StringVar()
        self.register_full_name = tk.StringVar()
        self.register_username = tk.StringVar()
        self.register_email = tk.StringVar()
        self.register_password = tk.StringVar()
        self.register_confirm = tk.StringVar()
        self.login_show_password = tk.BooleanVar(value=False)
        self.register_show_password = tk.BooleanVar(value=False)
        self.register_show_confirm = tk.BooleanVar(value=False)
        self.password_strength_var = tk.StringVar(value="Strength: -")

        self.setup_ui()

    def setup_ui(self):
        self.parent.configure(bg=COLORS["background"])

        root = tk.Frame(self.parent, bg=COLORS["background"])
        root.pack(fill=tk.BOTH, expand=True)
        self.root_container = root

        self.hero_panel = tk.Frame(root, bg=COLORS["primary"], width=480)
        self.hero_panel.pack(side=tk.LEFT, fill=tk.BOTH)
        self.hero_panel.pack_propagate(False)
        self._build_hero_panel()

        self.form_panel = tk.Frame(root, bg=COLORS["background"])
        self.form_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._build_form_panel()

        self.parent.bind("<Configure>", self._on_resize)

    def _build_hero_panel(self):
        for widget in self.hero_panel.winfo_children():
            widget.destroy()

        canvas = tk.Canvas(self.hero_panel, bg=COLORS["primary"], highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        def draw_background(event=None):
            canvas.delete("bg")
            w = max(1, canvas.winfo_width())
            h = max(1, canvas.winfo_height())
            stripe_colors = ["#1e3a8a", "#1d4ed8", "#2563eb", "#3b82f6"]
            stripe_h = max(24, h // 10)
            for i, c in enumerate(stripe_colors * 3):
                y0 = i * stripe_h
                y1 = y0 + stripe_h
                canvas.create_rectangle(0, y0, w, y1, fill=c, outline="", tags="bg")

            canvas.create_oval(w * 0.55, -h * 0.2, w * 1.35, h * 0.6, fill="#60a5fa", outline="", stipple="gray50", tags="bg")
            canvas.create_oval(-w * 0.4, h * 0.45, w * 0.6, h * 1.3, fill="#93c5fd", outline="", stipple="gray50", tags="bg")

        canvas.bind("<Configure>", draw_background)

        content = tk.Frame(canvas, bg=COLORS["primary"])
        canvas.create_window((0, 0), window=content, anchor="nw", width=460)

        tk.Label(content, text="OG CA", font=("Segoe UI", 34, "bold"), fg="white", bg=COLORS["primary"]).pack(anchor=tk.W, padx=34, pady=(48, 6))
        tk.Label(
            content,
            text="Next-generation financial cockpit",
            font=("Segoe UI", 14, "bold"),
            fg="#dbeafe",
            bg=COLORS["primary"],
        ).pack(anchor=tk.W, padx=34, pady=(0, 18))

        bullet_lines = [
            "Account-wise smart insights",
            "Goal planner + notification intelligence",
            "Transaction analytics and recurring automation",
            "Secure PBKDF2 password authentication",
        ]
        for line in bullet_lines:
            tk.Label(
                content,
                text=f"- {line}",
                font=("Segoe UI", 11),
                fg="white",
                bg=COLORS["primary"],
                justify=tk.LEFT,
            ).pack(anchor=tk.W, padx=36, pady=5)

        stat_bar = tk.Frame(content, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        stat_bar.pack(fill=tk.X, padx=34, pady=(28, 0))
        tk.Label(stat_bar, text="UI 2.0", font=("Segoe UI", 12, "bold"), bg=COLORS["surface"], fg=COLORS["primary"]).pack(side=tk.LEFT, padx=12, pady=10)
        tk.Label(stat_bar, text="Responsive + Smart + Fast", font=("Segoe UI", 10), bg=COLORS["surface"], fg=COLORS["text_secondary"]).pack(side=tk.RIGHT, padx=12)

    def _build_form_panel(self):
        for widget in self.form_panel.winfo_children():
            widget.destroy()

        wrapper = tk.Frame(self.form_panel, bg=COLORS["background"])
        wrapper.pack(fill=tk.BOTH, expand=True, padx=56, pady=42)

        card = tk.Frame(wrapper, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        card.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(card, bg=COLORS["surface"])
        header.pack(fill=tk.X, padx=26, pady=(24, 8))
        tk.Label(header, text="Welcome Back", font=("Segoe UI", 22, "bold"), fg=COLORS["text_primary"], bg=COLORS["surface"]).pack(anchor=tk.W)
        tk.Label(header, text="Sign in or create account to continue", font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=(4, 0))

        tab_bar = tk.Frame(card, bg=COLORS["surface"])
        tab_bar.pack(fill=tk.X, padx=26, pady=(6, 0))
        self.login_tab_btn = tk.Button(tab_bar, text="Login", command=lambda: self._switch_mode("login"), font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=14, pady=8)
        self.login_tab_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.register_tab_btn = tk.Button(tab_bar, text="Register", command=lambda: self._switch_mode("register"), font=("Segoe UI", 10, "bold"), relief=tk.FLAT, cursor="hand2", padx=14, pady=8)
        self.register_tab_btn.pack(side=tk.LEFT)

        self.login_frame = tk.Frame(card, bg=COLORS["surface"])
        self.register_frame = tk.Frame(card, bg=COLORS["surface"])
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=26, pady=(12, 24))

        self._build_login_form()
        self._build_register_form()
        self._switch_mode("login")

    def _build_login_form(self):
        tk.Label(self.login_frame, text="Username", font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=(0, 4))
        self.login_username_entry = ttk.Entry(self.login_frame, textvariable=self.login_username)
        self.login_username_entry.pack(fill=tk.X, pady=(0, 10), ipady=5)

        tk.Label(self.login_frame, text="Password", font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(anchor=tk.W, pady=(0, 4))
        self.login_password_entry = ttk.Entry(self.login_frame, textvariable=self.login_password, show="*")
        self.login_password_entry.pack(fill=tk.X, pady=(0, 8), ipady=5)
        self.login_username_entry.bind("<Return>", self._submit_login)
        self.login_password_entry.bind("<Return>", self._submit_login)

        tk.Checkbutton(
            self.login_frame,
            text="Show password",
            variable=self.login_show_password,
            command=self._toggle_login_password,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text_primary"],
            selectcolor=COLORS["surface"],
        ).pack(anchor=tk.W)

        tk.Button(
            self.login_frame,
            text="Sign In",
            command=lambda: self.handle_login(self.login_username.get(), self.login_password.get()),
            font=FONTS["button"],
            bg=COLORS["primary"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=10,
        ).pack(fill=tk.X, pady=(16, 0))

        helper = tk.Frame(self.login_frame, bg=COLORS["surface"])
        helper.pack(fill=tk.X, pady=(10, 0))
        tk.Button(
            helper, text="Use Demo Credentials", relief=tk.FLAT, cursor="hand2",
            bg=COLORS["surface_alt"], fg=COLORS["text_primary"], padx=10, pady=5,
            command=self._fill_demo_credentials
        ).pack(side=tk.LEFT)
        tk.Button(
            helper, text="Forgot Password Help", relief=tk.FLAT, cursor="hand2",
            bg=COLORS["surface_alt"], fg=COLORS["text_primary"], padx=10, pady=5,
            command=lambda: show_message(self.parent, "Password Help", "Use User Manager to reset account passwords securely.", "info")
        ).pack(side=tk.RIGHT)

    def _build_register_form(self):
        self.register_frame.columnconfigure(0, weight=1)
        self.register_frame.columnconfigure(1, weight=1)

        def add_label(text, row, col):
            tk.Label(self.register_frame, text=text, font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).grid(row=row, column=col, sticky="w", pady=(0, 4), padx=(0 if col == 0 else 10, 0))

        add_label("Full Name", 0, 0)
        add_label("Username", 0, 1)
        self.register_full_name_entry = ttk.Entry(self.register_frame, textvariable=self.register_full_name)
        self.register_full_name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10), ipady=5)
        self.register_username_entry = ttk.Entry(self.register_frame, textvariable=self.register_username)
        self.register_username_entry.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=(10, 0), ipady=5)

        tk.Label(self.register_frame, text="Email", font=FONTS["small"], fg=COLORS["text_secondary"], bg=COLORS["surface"]).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.register_email_entry = ttk.Entry(self.register_frame, textvariable=self.register_email)
        self.register_email_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10), ipady=5)

        add_label("Password", 4, 0)
        add_label("Confirm Password", 4, 1)
        self.register_password_entry = ttk.Entry(self.register_frame, textvariable=self.register_password, show="*")
        self.register_password_entry.grid(row=5, column=0, sticky="ew", pady=(0, 8), ipady=5)
        self.register_confirm_entry = ttk.Entry(self.register_frame, textvariable=self.register_confirm, show="*")
        self.register_confirm_entry.grid(row=5, column=1, sticky="ew", pady=(0, 8), padx=(10, 0), ipady=5)
        self.register_full_name_entry.bind("<Return>", self._submit_register)
        self.register_username_entry.bind("<Return>", self._submit_register)
        self.register_email_entry.bind("<Return>", self._submit_register)
        self.register_password_entry.bind("<Return>", self._submit_register)
        self.register_confirm_entry.bind("<Return>", self._submit_register)

        self.register_password_entry.bind("<KeyRelease>", self._update_password_strength)

        toggle_row = tk.Frame(self.register_frame, bg=COLORS["surface"])
        toggle_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tk.Checkbutton(
            toggle_row,
            text="Show password",
            variable=self.register_show_password,
            command=self._toggle_register_password,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text_primary"],
            selectcolor=COLORS["surface"],
        ).pack(side=tk.LEFT)
        tk.Checkbutton(
            toggle_row,
            text="Show confirm",
            variable=self.register_show_confirm,
            command=self._toggle_register_confirm,
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text_primary"],
            selectcolor=COLORS["surface"],
        ).pack(side=tk.LEFT, padx=(10, 0))

        tk.Label(self.register_frame, textvariable=self.password_strength_var, font=FONTS["small"], fg=COLORS["primary"], bg=COLORS["surface"]).grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 8))

        tk.Button(
            self.register_frame,
            text="Create Account",
            command=lambda: self.handle_register(
                self.register_full_name.get(),
                self.register_username.get(),
                self.register_email.get(),
                self.register_password.get(),
                self.register_confirm.get(),
            ),
            font=FONTS["button"],
            bg=COLORS["accent"],
            fg="white",
            relief=tk.FLAT,
            cursor="hand2",
            padx=16,
            pady=10,
        ).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(4, 0))

        tk.Label(
            self.register_frame,
            text="By creating an account you agree to secure local data processing.",
            font=FONTS["small"],
            fg=COLORS["text_secondary"],
            bg=COLORS["surface"]
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _switch_mode(self, mode):
        self.current_mode = mode
        active_bg = COLORS["primary"]
        inactive_bg = COLORS["surface_alt"]

        if mode == "login":
            self.login_tab_btn.config(bg=active_bg, fg="white")
            self.register_tab_btn.config(bg=inactive_bg, fg=COLORS["text_primary"])
            self.register_frame.pack_forget()
            self.login_frame.pack(fill=tk.BOTH, expand=True, padx=26, pady=(12, 24))
        else:
            self.register_tab_btn.config(bg=active_bg, fg="white")
            self.login_tab_btn.config(bg=inactive_bg, fg=COLORS["text_primary"])
            self.login_frame.pack_forget()
            self.register_frame.pack(fill=tk.BOTH, expand=True, padx=26, pady=(12, 24))

    def _toggle_login_password(self):
        self.login_password_entry.config(show="" if self.login_show_password.get() else "*")

    def _toggle_register_password(self):
        self.register_password_entry.config(show="" if self.register_show_password.get() else "*")

    def _toggle_register_confirm(self):
        self.register_confirm_entry.config(show="" if self.register_show_confirm.get() else "*")

    def _update_password_strength(self, event=None):
        password = self.register_password.get()
        score = 0
        if len(password) >= 8:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(not c.isalnum() for c in password):
            score += 1

        levels = {
            0: "Strength: Very Weak",
            1: "Strength: Weak",
            2: "Strength: Fair",
            3: "Strength: Good",
            4: "Strength: Strong",
            5: "Strength: Very Strong",
        }
        self.password_strength_var.set(levels.get(score, "Strength: -"))

    def _fill_demo_credentials(self):
        self.login_username.set("admin")
        self.login_password.set("Admin@123")

    def _submit_login(self, event=None):
        self.handle_login(self.login_username.get(), self.login_password.get())

    def _submit_register(self, event=None):
        self.handle_register(
            self.register_full_name.get(),
            self.register_username.get(),
            self.register_email.get(),
            self.register_password.get(),
            self.register_confirm.get(),
        )

    def _on_resize(self, event=None):
        width = self.parent.winfo_width()
        compact = width < 1080
        if compact == self._auth_compact:
            return

        self._auth_compact = compact
        self.hero_panel.pack_forget()
        self.form_panel.pack_forget()

        if compact:
            self.hero_panel.configure(height=220, width=1)
            self.hero_panel.pack(side=tk.TOP, fill=tk.X)
            self.form_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        else:
            self.hero_panel.configure(width=480, height=1)
            self.hero_panel.pack(side=tk.LEFT, fill=tk.BOTH)
            self.form_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def handle_login(self, username, password):
        username = (username or "").strip()
        if not username or not password:
            show_message(self.parent, "Error", "Username and password are required", "error")
            return

        try:
            user_data = self.db.login_user(username, password)
            if not user_data:
                show_message(self.parent, "Error", "Invalid username or password", "error")
                return
            self.on_login_success(user_data)
        except Exception as e:
            show_message(self.parent, "Error", f"Login failed: {str(e)}", "error")

    def handle_register(self, full_name, username, email, password, confirm):
        full_name = (full_name or "").strip()
        username = (username or "").strip()
        email = (email or "").strip()

        if not all([full_name, username, email, password, confirm]):
            show_message(self.parent, "Error", "All fields are required", "error")
            return

        if password != confirm:
            show_message(self.parent, "Error", "Passwords do not match", "error")
            return

        if not validate_email(email):
            show_message(self.parent, "Error", "Invalid email address", "error")
            return

        valid, message = validate_password(password)
        if not valid:
            show_message(self.parent, "Error", message, "error")
            return

        try:
            user_id = self.db.register_user(username, email, password, full_name)
            if not user_id:
                show_message(self.parent, "Error", "Username or email already exists", "error")
                return
            show_message(self.parent, "Success", "Account created successfully", "info")
            self.register_full_name.set("")
            self.register_username.set("")
            self.register_email.set("")
            self.register_password.set("")
            self.register_confirm.set("")
            self._switch_mode("login")
        except Exception as e:
            show_message(self.parent, "Error", f"Registration failed: {str(e)}", "error")
