"""Standalone user database management application."""
import tkinter as tk
from tkinter import ttk, messagebox

from config import COLORS, FONTS
from database import Database
from utils import validate_email, validate_password


class UserManagerApp:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.selected_user_id = None

        self.root.title("OG CA - User Manager")
        self.root.geometry("1200x740")
        self.root.minsize(980, 620)
        self.root.configure(bg=COLORS["background"])

        self._configure_theme()
        self._build_ui()
        self.refresh_users()

    def _configure_theme(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", rowheight=28, font=FONTS["small"])
        style.configure("Treeview.Heading", font=FONTS["body"], background=COLORS["primary"], foreground="white")

    def _build_ui(self):
        header = tk.Frame(self.root, bg=COLORS["surface"])
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="User Database Manager",
            font=FONTS["heading"],
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
        ).pack(side=tk.LEFT, padx=18, pady=14)

        toolbar = tk.Frame(self.root, bg=COLORS["background"])
        toolbar.pack(fill=tk.X, padx=16, pady=(12, 8))

        tk.Label(toolbar, text="Search:", font=FONTS["body"], bg=COLORS["background"], fg=COLORS["text_primary"]).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=34)
        self.search_entry.pack(side=tk.LEFT, padx=(8, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_users())

        ttk.Button(toolbar, text="Refresh", command=self.refresh_users).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="New User", command=self.start_new_user).pack(side=tk.LEFT, padx=4)

        body = tk.Frame(self.root, bg=COLORS["background"])
        body.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        list_card = tk.Frame(body, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        cols = ("id", "username", "email", "full_name", "phone", "city", "state", "created_at")
        self.tree = ttk.Treeview(list_card, columns=cols, show="headings")
        for col, title, width in [
            ("id", "ID", 60),
            ("username", "Username", 130),
            ("email", "Email", 200),
            ("full_name", "Full Name", 150),
            ("phone", "Phone", 110),
            ("city", "City", 90),
            ("state", "State", 80),
            ("created_at", "Created", 140),
        ]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(list_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_user_select)

        form_card = tk.Frame(body, bg=COLORS["surface"], relief=tk.FLAT, bd=1)
        form_card.grid(row=0, column=1, sticky="nsew")

        tk.Label(form_card, text="User Details", font=FONTS["subheading"], bg=COLORS["surface"], fg=COLORS["text_primary"]).pack(anchor=tk.W, padx=14, pady=(14, 8))

        form = tk.Frame(form_card, bg=COLORS["surface"])
        form.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        self.form_vars = {
            "id": tk.StringVar(),
            "username": tk.StringVar(),
            "email": tk.StringVar(),
            "full_name": tk.StringVar(),
            "phone": tk.StringVar(),
            "address": tk.StringVar(),
            "city": tk.StringVar(),
            "state": tk.StringVar(),
            "zip_code": tk.StringVar(),
            "password": tk.StringVar(),
            "confirm": tk.StringVar(),
        }

        fields = [
            ("id", "User ID", True),
            ("username", "Username", False),
            ("email", "Email", False),
            ("full_name", "Full Name", False),
            ("phone", "Phone", False),
            ("address", "Address", False),
            ("city", "City", False),
            ("state", "State", False),
            ("zip_code", "Zip Code", False),
            ("password", "Password", False),
            ("confirm", "Confirm Password", False),
        ]

        self.form_entries = {}
        for idx, (key, label, readonly) in enumerate(fields):
            tk.Label(form, text=label, font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["text_secondary"]).grid(row=idx, column=0, sticky="w", pady=(0, 3))
            show = "*" if key in {"password", "confirm"} else ""
            entry = ttk.Entry(form, textvariable=self.form_vars[key], show=show)
            if readonly:
                entry.configure(state="readonly")
            entry.grid(row=idx, column=1, sticky="ew", pady=(0, 8))
            self.form_entries[key] = entry

        form.grid_columnconfigure(1, weight=1)

        actions = tk.Frame(form_card, bg=COLORS["surface"])
        actions.pack(fill=tk.X, padx=14, pady=(2, 14))

        ttk.Button(actions, text="Save User", command=self.save_user).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Delete User", command=self.delete_selected_user).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Reset Password", command=self.reset_password_only).pack(side=tk.LEFT, padx=3)
        ttk.Button(actions, text="Clear Form", command=self.start_new_user).pack(side=tk.LEFT, padx=3)

        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, font=FONTS["small"], bg=COLORS["surface"], fg=COLORS["text_secondary"], anchor="w")
        status.pack(fill=tk.X, padx=0, pady=(0, 0), ipady=6)

    def set_status(self, text):
        self.status_var.set(text)

    def refresh_users(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = self.db.get_all_users(self.search_var.get().strip())
        for user in rows:
            self.tree.insert(
                "",
                tk.END,
                iid=str(user["id"]),
                values=(
                    user["id"],
                    user.get("username", ""),
                    user.get("email", ""),
                    user.get("full_name", ""),
                    user.get("phone", ""),
                    user.get("city", ""),
                    user.get("state", ""),
                    user.get("created_at", ""),
                ),
            )

        self.set_status(f"Loaded {len(rows)} user(s)")

    def on_user_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        user_id = int(selected[0])
        user = self.db.get_user(user_id)
        if not user:
            return

        self.selected_user_id = user_id
        self.form_entries["id"].configure(state="normal")
        self.form_vars["id"].set(str(user.get("id", "")))
        self.form_entries["id"].configure(state="readonly")
        for key in ("username", "email", "full_name", "phone", "address", "city", "state", "zip_code"):
            self.form_vars[key].set(str(user.get(key, "") or ""))

        self.form_vars["password"].set("")
        self.form_vars["confirm"].set("")
        self.set_status(f"Editing user #{user_id}")

    def start_new_user(self):
        self.selected_user_id = None
        for key, var in self.form_vars.items():
            var.set("")
        self.tree.selection_remove(self.tree.selection())
        self.set_status("New user mode")

    def _validate_form(self, require_password):
        username = self.form_vars["username"].get().strip()
        email = self.form_vars["email"].get().strip()
        password = self.form_vars["password"].get()
        confirm = self.form_vars["confirm"].get()

        if not username:
            messagebox.showerror("Validation", "Username is required")
            return None
        if not email or not validate_email(email):
            messagebox.showerror("Validation", "Valid email is required")
            return None

        if require_password or password or confirm:
            if password != confirm:
                messagebox.showerror("Validation", "Password and confirm password do not match")
                return None
            valid, message = validate_password(password)
            if not valid:
                messagebox.showerror("Validation", message)
                return None

        data = {
            "username": username,
            "email": email,
            "full_name": self.form_vars["full_name"].get().strip(),
            "phone": self.form_vars["phone"].get().strip(),
            "address": self.form_vars["address"].get().strip(),
            "city": self.form_vars["city"].get().strip(),
            "state": self.form_vars["state"].get().strip(),
            "zip_code": self.form_vars["zip_code"].get().strip(),
            "password": password,
        }
        return data

    def save_user(self):
        creating = self.selected_user_id is None
        data = self._validate_form(require_password=creating)
        if not data:
            return

        if creating:
            user_id = self.db.register_user(data["username"], data["email"], data["password"], data["full_name"])
            if not user_id:
                messagebox.showerror("Error", "Could not create user. Username/email may already exist.")
                return

            self.db.update_user_admin(
                user_id,
                phone=data["phone"],
                address=data["address"],
                city=data["city"],
                state=data["state"],
                zip_code=data["zip_code"],
            )
            self.set_status(f"Created user #{user_id}")
            messagebox.showinfo("Success", "User created successfully")
            self.selected_user_id = user_id
        else:
            ok = self.db.update_user_admin(
                self.selected_user_id,
                username=data["username"],
                email=data["email"],
                full_name=data["full_name"],
                phone=data["phone"],
                address=data["address"],
                city=data["city"],
                state=data["state"],
                zip_code=data["zip_code"],
            )
            if not ok:
                messagebox.showerror("Error", "Update failed. Username/email may already exist.")
                return

            if data["password"]:
                self.db.update_user_password(self.selected_user_id, data["password"])

            self.set_status(f"Updated user #{self.selected_user_id}")
            messagebox.showinfo("Success", "User updated successfully")

        self.refresh_users()

    def reset_password_only(self):
        if self.selected_user_id is None:
            messagebox.showerror("Error", "Select a user first")
            return

        password = self.form_vars["password"].get()
        confirm = self.form_vars["confirm"].get()
        if not password:
            messagebox.showerror("Error", "Enter a new password")
            return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return

        valid, message = validate_password(password)
        if not valid:
            messagebox.showerror("Error", message)
            return

        if self.db.update_user_password(self.selected_user_id, password):
            self.form_vars["password"].set("")
            self.form_vars["confirm"].set("")
            self.set_status(f"Password reset for user #{self.selected_user_id}")
            messagebox.showinfo("Success", "Password updated")

    def delete_selected_user(self):
        if self.selected_user_id is None:
            messagebox.showerror("Error", "Select a user first")
            return

        answer = messagebox.askyesno(
            "Confirm Delete",
            f"Delete user #{self.selected_user_id}? This will remove all linked data.",
        )
        if not answer:
            return

        if self.db.delete_user(self.selected_user_id):
            messagebox.showinfo("Success", "User deleted")
            self.set_status("User deleted")
            self.start_new_user()
            self.refresh_users()
        else:
            messagebox.showerror("Error", "Delete failed")


def main():
    root = tk.Tk()
    UserManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
