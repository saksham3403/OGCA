"""Main Application Entry Point"""
import tkinter as tk
from config import WINDOW_WIDTH, WINDOW_HEIGHT, COLORS
from auth_ui import AuthenticationUI
from expense_tracker import ExpenseTrackerUI


class ExpenseTrackerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OG CA")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(1000, 600)
        self.root.config(bg=COLORS["background"])
        
        # Center window on screen
        self.center_window()
        
        # Start with authentication
        self.show_auth()

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')

    def show_auth(self):
        """Show authentication screen"""
        # Clear root
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create authentication UI
        auth_frame = tk.Frame(self.root, bg=COLORS["background"])
        auth_frame.pack(fill=tk.BOTH, expand=True)
        
        auth_ui = AuthenticationUI(auth_frame, self.on_login_success)

    def on_login_success(self, user_data):
        """Handle successful login"""
        # Clear root
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create expense tracker UI
        tracker_frame = tk.Frame(self.root, bg=COLORS["background"])
        tracker_frame.pack(fill=tk.BOTH, expand=True)
        
        expense_tracker = ExpenseTrackerUI(tracker_frame, user_data)
        self.show_welcome_popup(user_data)

    def show_welcome_popup(self, user_data):
        """Display a polished welcome popup after login."""
        username = user_data.get("username") or user_data.get("full_name") or "User"
        popup = tk.Toplevel(self.root)
        popup.title("Welcome")
        popup.geometry("420x180")
        popup.configure(bg=COLORS["primary"])
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + 60
        popup.geometry(f"+{x}+{y}")

        card = tk.Frame(popup, bg=COLORS["primary"])
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        tk.Frame(card, bg=COLORS["accent"], height=5).pack(fill=tk.X)
        tk.Label(
            card,
            text=f"Welcome {username}",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg=COLORS["primary"]
        ).pack(pady=(25, 8))
        tk.Label(
            card,
            text="OG CA is ready",
            font=("Segoe UI", 11),
            fg="#dbeafe",
            bg=COLORS["primary"]
        ).pack()

        popup.after(2200, popup.destroy)

    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ExpenseTrackerApp()
    app.run()
