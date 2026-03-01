"""Comprehensive Utility functions for Expense Tracker Pro"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS, FONTS
from datetime import datetime, timedelta
import re


# ============== CUSTOM UI COMPONENTS ==============

class CustomButton(tk.Canvas):
    """Premium custom styled button with hover effects"""
    def __init__(self, parent, text, command=None, bg_color=COLORS["primary"], 
                 text_color="white", width=120, height=35, **kwargs):
        tk.Canvas.__init__(self, parent, width=width, height=height, bg=parent['bg'],
                          highlightthickness=0, **kwargs)
        self.config(cursor="hand2")
        self.command = command
        self.bg_color = bg_color
        self.text_color = text_color
        self.text = text
        self.width = width
        self.height = height
        self.is_hover = False
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self._draw_button()

    def _draw_button(self):
        self.delete("all")
        color = self._get_color()
        self.create_rectangle(2, 2, self.width-2, self.height-2, 
                            fill=color, outline=color)
        self.create_text(self.width/2, self.height/2, text=self.text,
                        fill=self.text_color, font=FONTS["body"])

    def _get_color(self):
        return lighten_color(self.bg_color) if self.is_hover else self.bg_color

    def _on_enter(self, e):
        self.is_hover = True
        self._draw_button()

    def _on_leave(self, e):
        self.is_hover = False
        self._draw_button()

    def _on_click(self, e):
        if self.command:
            self.command()


class PremiumButton(tk.Button):
    """Premium button with professional styling"""
    def __init__(self, parent, text, command=None, **kwargs):
        defaults = {
            'font': FONTS["button"],
            'bg': COLORS["primary"],
            'fg': "white",
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'padx': 15,
            'pady': 10,
            'activebackground': lighten_color(COLORS["primary"]),
        }
        defaults.update(kwargs)
        tk.Button.__init__(self, parent, text=text, command=command, **defaults)


class CustomEntry(tk.Frame):
    """Custom styled entry widget with placeholder support"""
    def __init__(self, parent, placeholder="", show=None, **kwargs):
        tk.Frame.__init__(self, parent, bg=COLORS["background"], **kwargs)
        
        self.entry = tk.Entry(self, font=FONTS["body"], show=show,
                            fg=COLORS["text_primary"], bg=COLORS["surface"],
                            relief=tk.FLAT, bd=0)
        self.entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.placeholder = placeholder
        self.placeholder_active = False
        
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)
            self.placeholder_active = True

    def _on_focus_in(self, e):
        if self.placeholder_active:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=COLORS["text_primary"])
            self.placeholder_active = False

    def _on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=COLORS["text_secondary"])
            self.placeholder_active = True

    def get(self):
        value = self.entry.get()
        if self.placeholder_active:
            return ""
        return value

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.placeholder_active = False

    def clear(self):
        self.entry.delete(0, tk.END)
        if self.placeholder:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=COLORS["text_secondary"])
            self.placeholder_active = True


class Badge(tk.Label):
    """Badge/label component for categorization"""
    def __init__(self, parent, text, bg_color=COLORS["secondary"], **kwargs):
        defaults = {
            'text': text,
            'bg': bg_color,
            'fg': 'white',
            'font': FONTS["small"],
            'padx': 8,
            'pady': 4,
            'relief': tk.FLAT,
        }
        defaults.update(kwargs)
        tk.Label.__init__(self, parent, **defaults)


class ProgressBar(tk.Frame):
    """Custom progress bar component"""
    def __init__(self, parent, value=0, max_value=100, height=8, **kwargs):
        tk.Frame.__init__(self, parent, bg=COLORS["border"], height=height, **kwargs)
        self.max_value = max_value
        self.value = value
        
        self.canvas = tk.Canvas(self, bg=COLORS["border"], height=height, 
                               highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.pack_propagate(False)
        
        self._update_bar()
    
    def set_value(self, value):
        self.value = min(value, self.max_value)
        self._update_bar()
    
    def _update_bar(self):
        self.canvas.delete("all")
        percentage = (self.value / self.max_value) if self.max_value > 0 else 0
        bar_color = self._get_bar_color(percentage)
        
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width() * percentage, 
                                    self.canvas.winfo_height(),
                                    fill=bar_color, outline=bar_color)
    
    def _get_bar_color(self, percentage):
        if percentage > 0.95:
            return COLORS["danger"]
        elif percentage > 0.80:
            return COLORS["warning"]
        else:
            return COLORS["accent"]


class RoundedFrame(tk.Frame):
    """Frame with styling"""
    def __init__(self, parent, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.config(relief=tk.FLAT, bd=1, bg=COLORS["border"])


class StatPill(tk.Frame):
    """Statistics pill component"""
    def __init__(self, parent, label, value, color=COLORS["primary"], **kwargs):
        tk.Frame.__init__(self, parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1, **kwargs)
        
        tk.Label(self, text=label, font=FONTS["small"],
                fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(pady=(8, 4))
        
        tk.Label(self, text=str(value), font=(FONTS["heading"][0], 14, 'bold'),
                fg=color, bg=COLORS["surface"]).pack(pady=(4, 8))


class MetricCard(tk.Frame):
    """Enhanced metric card with icon and status"""
    def __init__(self, parent, title, value, subtitle="", icon_color=COLORS["primary"], **kwargs):
        tk.Frame.__init__(self, parent, bg=COLORS["surface"], relief=tk.FLAT, bd=1, **kwargs)
        
        # Header
        header = tk.Frame(self, bg=COLORS["surface"])
        header.pack(fill=tk.X, padx=12, pady=(12, 0))
        
        tk.Label(header, text=title, font=FONTS["small"],
                fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(side=tk.LEFT)
        
        # Value
        tk.Label(self, text=str(value), font=(FONTS["title"][0], 16, 'bold'),
                fg=icon_color, bg=COLORS["surface"]).pack(pady=8)
        
        # Subtitle
        if subtitle:
            tk.Label(self, text=subtitle, font=FONTS["small"],
                    fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(pady=(0, 12))


# ============== LAYOUT & HEADER COMPONENTS ==============

def create_header(parent, title, subtitle=""):
    """Create a professional header section with a colored accent bar"""
    frame = tk.Frame(parent, bg=COLORS["background"])
    frame.pack(fill=tk.X, padx=20, pady=(20, 10))

    # colored accent to the left of title
    accent = tk.Frame(frame, bg=COLORS["accent"], width=5)
    accent.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))

    text_container = tk.Frame(frame, bg=COLORS["background"])
    text_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

    tk.Label(text_container, text=title, font=FONTS["heading"], 
            fg=COLORS["text_primary"], bg=COLORS["background"]).pack(anchor=tk.W)
    
    if subtitle:
        tk.Label(text_container, text=subtitle, font=FONTS["small"], 
                fg=COLORS["text_secondary"], bg=COLORS["background"]).pack(anchor=tk.W)
    
    return frame


def create_stat_card(parent, label, value, color=COLORS["primary"]):
    """Create a statistic card with enhanced styling"""
    frame = tk.Frame(parent, bg=COLORS["surface"], relief=tk.RIDGE, bd=2)
    frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)
    
    tk.Label(frame, text=label, font=FONTS["small"],
            fg=COLORS["text_secondary"], bg=COLORS["surface"]).pack(pady=(10, 5))
    
    tk.Label(frame, text=value, font=FONTS["title"],
            fg=color, bg=COLORS["surface"]).pack(pady=(5, 10))
    
    return frame


def create_section_divider(parent):
    """Create a visual divider"""
    divider = tk.Frame(parent, bg=COLORS["border"], height=1)
    divider.pack(fill=tk.X, padx=20, pady=10)
    divider.pack_propagate(False)


# ============== FORMATTING UTILITIES ==============

def format_currency(value):
    """Format number as currency"""
    return f"₹{value:,.2f}"


def format_date(date_obj):
    """Format date object or string"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%d %b %Y")


def format_percent(value, total):
    """Calculate and format percentage"""
    if total == 0:
        return 0
    return round((value / total) * 100, 1)


def format_time(seconds):
    """Format seconds to readable time"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_large_number(num):
    """Format large numbers"""
    if num >= 1000000:
        return f"₹{num/1000000:.1f}Cr"
    elif num >= 100000:
        return f"₹{num/100000:.1f}L"
    elif num >= 1000:
        return f"₹{num/1000:.1f}K"
    else:
        return f"₹{num:.0f}"


def abbreviate_text(text, length=30):
    """Abbreviate text with ellipsis"""
    if len(text) > length:
        return text[:length-3] + "..."
    return text


# ============== VALIDATION UTILITIES ==============

def validate_email(email):
    """Comprehensive email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain digit"
    return True, "Password is strong"


def validate_phone(phone):
    """Validate phone number"""
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, phone.replace("-", "").replace(" ", "")) is not None


def validate_amount(amount):
    """Validate currency amount"""
    try:
        val = float(amount)
        return val > 0, "Amount must be greater than 0"
    except ValueError:
        return False, "Invalid amount format"


def validate_date(date_str, fmt='%Y-%m-%d'):
    """Validate date format"""
    try:
        datetime.strptime(date_str, fmt)
        return True, "Valid date"
    except ValueError:
        return False, f"Invalid date format (use {fmt})"


def validate_required_field(value):
    """Validate field is not empty"""
    return bool(value.strip()), "This field is required"


# ============== MESSAGE & DIALOG UTILITIES ==============

def show_message(parent, title, message, msg_type="info"):
    """Show message dialog"""
    if msg_type == "info":
        messagebox.showinfo(title, message)
    elif msg_type == "error":
        messagebox.showerror(title, message)
    elif msg_type == "warning":
        messagebox.showwarning(title, message)
    else:
        return messagebox.askyesno(title, message)


def show_success(parent, message):
    """Show success message"""
    messagebox.showinfo("Success", message)


def show_error(parent, message):
    """Show error message"""
    messagebox.showerror("Error", message)


def show_warning(parent, message):
    """Show warning message"""
    messagebox.showwarning("Warning", message)


def ask_confirmation(parent, title, message):
    """Ask for user confirmation"""
    return messagebox.askyesno(title, message)


# ============== DATE & TIME UTILITIES ==============

def get_date_range(period="month"):
    """Get date range for reports"""
    end_date = datetime.now().date()
    
    if period == "week":
        start_date = end_date - timedelta(days=7)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "quarter":
        start_date = end_date - timedelta(days=90)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    elif period == "all":
        start_date = end_date - timedelta(days=3650)  # 10 years
    else:
        start_date = end_date - timedelta(days=30)
    
    return str(start_date), str(end_date)


def get_current_month_range():
    """Get current month date range"""
    today = datetime.now().date()
    first_day = today.replace(day=1)
    return str(first_day), str(today)


def get_date_label(date_str):
    """Get human-readable date label"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        days_ago = (datetime.now().date() - date_obj.date()).days
        
        if days_ago == 0:
            return "Today"
        elif days_ago == 1:
            return "Yesterday"
        elif days_ago < 7:
            return f"{days_ago} days ago"
        elif days_ago < 30:
            weeks = days_ago // 7
            return f"{weeks} weeks ago"
        else:
            months = days_ago // 30
            return f"{months} months ago"
    except:
        return date_str


# ============== COLOR & STYLING UTILITIES ==============

def lighten_color(hex_color, factor=1.2):
    """Lighten a hex color"""
    hex_color = hex_color.lstrip('#')
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(min(255, int(c * factor)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    except:
        return hex_color


def darken_color(hex_color, factor=0.8):
    """Darken a hex color"""
    hex_color = hex_color.lstrip('#')
    try:
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb = tuple(max(0, int(c * factor)) for c in rgb)
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    except:
        return hex_color


def get_status_color(value, good_threshold=50, warn_threshold=80):
    """Get color based on value status"""
    if value >= warn_threshold:
        return COLORS["danger"]
    elif value >= good_threshold:
        return COLORS["warning"]
    else:
        return COLORS["accent"]


# ============== CATEGORY & ANALYTICS UTILITIES ==============

def get_category_icon(category):
    """Get icon for category"""
    icons = {
        "Food & Dining": "🍔",
        "Groceries": "🛒",
        "Transportation": "🚗",
        "Shopping": "🛍",
        "Entertainment": "🎬",
        "Bills & Utilities": "💡",
        "Home & Rent": "🏠",
        "Health & Fitness": "💪",
        "Education": "📚",
        "Travel": "✈",
        "Work & Office": "💼",
        "Personal Care": "💅",
        "Insurance": "🛡",
        "Gifts & Charity": "🎁",
    }
    return icons.get(category, "•")


def truncate_decimal(value, decimals=2):
    """Truncate decimal places"""
    multiplier = 10 ** decimals
    return int(value * multiplier) / multiplier


# ============== DATA GENERATION UTILITIES ==============

def generate_summary_stats(db, user_id):
    """Generate comprehensive summary statistics"""
    summary = db.get_summary(user_id)
    stats = {
        'total_income': format_currency(summary['total_income']),
        'total_expenses': format_currency(summary['total_expenses']),
        'balance': format_currency(summary['balance']),
        'balance_raw': summary['balance'],
        'savings_rate': f"{(summary['balance']/summary['total_income']*100 if summary['total_income'] > 0 else 0):.1f}%",
        'expense_ratio': f"{(summary['total_expenses']/summary['total_income']*100 if summary['total_income'] > 0 else 0):.1f}%",
    }
    return stats


# ============== FILE & EXPORT UTILITIES ==============

def safe_filename(filename):
    """Make filename safe for filesystem"""
    import re
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    return filename.replace(' ', '_')


def get_export_filename(report_type, format_type='pdf'):
    """Generate export filename"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{report_type}_{timestamp}.{format_type}"


# ============== THEME MANAGEMENT ==============

def apply_theme(theme="light"):
    """Apply light or dark theme by updating COLORS in config"""
    import config
    # update the main COLORS dict from config; this affects UI components
    if theme == "dark":
        for key, val in config.COLORS_DARK.items():
            config.COLORS[key] = val
        config.CURRENT_THEME = "dark"
    else:
        # revert to original light palette by reloading defaults
        for key, val in config.COLORS_LIGHT.items():
            config.COLORS[key] = val
        config.CURRENT_THEME = "light"


# ============== NEW UI COMPONENTS ==============

class Sidebar(tk.Frame):
    """Sidebar navigation container"""
    def __init__(self, parent, width=200, **kwargs):
        tk.Frame.__init__(self, parent, width=width, bg=COLORS["surface"] if CURRENT_THEME=="light" else COLORS["surface_alt"], **kwargs)
        self.pack_propagate(False)

    def add_button(self, text, command, icon=None):
        btn = tk.Button(self, text=text, command=command,
                        bg=COLORS["surface"], fg=COLORS["text_primary"],
                        font=FONTS["body"], relief=tk.FLAT, anchor="w", padx=20,
                        cursor="hand2")
        btn.pack(fill=tk.X, pady=2)
        return btn


class Modal(tk.Toplevel):
    """Simple modal window"""
    def __init__(self, parent, title="", **kwargs):
        tk.Toplevel.__init__(self, parent, **kwargs)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=COLORS["background"])
        self.resizable(False, False)

    def close(self):
        self.grab_release()
        self.destroy()


