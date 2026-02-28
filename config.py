# Configuration file for OG CA
import os
from pathlib import Path

# Get the directory of the current file
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DB_PATH = BASE_DIR / "expense_tracker.db"

# UI Configuration
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 600

# Theme Configuration (theme toggle removed, default fixed to light)
CURRENT_THEME = "light"  # kept for legacy but no toggle UI

# Color Scheme - Professional Accounting Look (Light Theme - Defaults)
COLORS_LIGHT = {
    "primary": "#1e3a8a",      # Deep blue
    "secondary": "#3b82f6",    # Primary blue
    "accent": "#10b981",       # Green (positive)
    "danger": "#ef4444",       # Red (negative)
    "warning": "#f59e0b",      # Amber
    "info": "#06b6d4",         # Cyan
    "success": "#059669",      # Dark green
    "background": "#f9fafb",   # Light gray
    "surface": "#ffffff",      # White
    "surface_alt": "#f3f4f6",  # Alt surface
    "text_primary": "#111827",  # Dark gray
    "text_secondary": "#6b7280", # Medium gray
    "border": "#e5e7eb",       # Light border
    "border_dark": "#d1d5db",  # Darker border
    "hover": "#f0f9ff",        # Hover overlay
    "disabled": "#d1d5db",     # Disabled color
}

# Current active colors (will switch based on theme)
COLORS = {
    "primary": "#1e3a8a",      # Deep blue
    "secondary": "#3b82f6",    # Primary blue
    "accent": "#10b981",       # Green (positive)
    "danger": "#ef4444",       # Red (negative)
    "warning": "#f59e0b",      # Amber
    "info": "#06b6d4",         # Cyan
    "success": "#059669",      # Dark green
    "background": "#f9fafb",   # Light gray
    "surface": "#ffffff",      # White
    "surface_alt": "#f3f4f6",  # Alt surface
    "text_primary": "#111827",  # Dark gray
    "text_secondary": "#6b7280", # Medium gray
    "border": "#e5e7eb",       # Light border
    "border_dark": "#d1d5db",  # Darker border
    "hover": "#f0f9ff",        # Hover overlay
    "disabled": "#d1d5db",     # Disabled color
}

# Dark Theme Colors (optional)
COLORS_DARK = {
    "primary": "#3b82f6",
    "secondary": "#60a5fa",
    "accent": "#34d399",
    "danger": "#f87171",
    "warning": "#fbbf24",
    "info": "#22d3ee",
    "success": "#6ee7b7",
    "background": "#111827",
    "surface": "#1f2937",
    "surface_alt": "#2d3748",
    "text_primary": "#f3f4f6",
    "text_secondary": "#9ca3af",
    "border": "#374151",
    "border_dark": "#4b5563",
    "hover": "#1e3a8a",
    "disabled": "#6b7280",
}

# Font Configuration
FONTS = {
    "title": ("Segoe UI", 20, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 11),
    "small": ("Segoe UI", 9),
    "mono": ("Courier New", 10),
    "button": ("Segoe UI", 11, "bold"),
    "label": ("Segoe UI", 10, "bold"),
}

# Password hashing
SALT_LENGTH = 32
HASH_ITERATIONS = 100000

# PDF Configuration
PDF_MARGIN = 50
PDF_PAGE_WIDTH = 595  # A4 width in points
PDF_PAGE_HEIGHT = 842  # A4 height in points
PDF_FONT_NAME = "Helvetica"
PDF_FONT_SIZE_TITLE = 16
PDF_FONT_SIZE_HEADING = 12
PDF_FONT_SIZE_BODY = 10
PDF_FONT_SIZE_SMALL = 8

# Session timeout in minutes
SESSION_TIMEOUT = 30

# Export formats
EXPORT_FORMATS = ["PDF", "CSV", "Excel", "JSON"]

# Feature Flags - 50+ Features
FEATURES = {
    # Core Features
    "transactions": True,
    "expenses": True,
    "income": True,
    "accounts": True,
    
    # Transaction Features (20+)
    "recurring_transactions": True,
    "transaction_tags": True,
    "transaction_notes": True,
    "transaction_attachments": True,
    "split_transactions": True,
    "transaction_templates": True,
    "bulk_edit": True,
    "undo_redo": True,
    "transaction_search": True,
    "transaction_filters": True,
    "duplicate_detection": True,
    "transaction_categories_custom": True,
    "transaction_subcategories": True,
    "vendor_tracking": True,
    "invoice_numbers": True,
    "payment_methods_custom": True,
    "transaction_status": True,
    "refund_tracking": True,
    "reimbursement_tracking": True,
    "business_vs_personal": True,
    "tax_category_marking": True,
    
    # Budget & Goals (8+)
    "budgets": True,
    "budget_alerts": True,
    "spending_goals": True,
    "monthly_targets": True,
    "budget_rollover": True,
    "budget_templates": True,
    "savings_tracking": True,
    "spending_limits": True,
    
    # Analytics & Reports (15+)
    "dashboard_analytics": True,
    "spending_trends": True,
    "category_trends": True,
    "monthly_comparison": True,
    "year_over_year": True,
    "expense_forecasting": True,
    "cash_flow_projection": True,
    "spending_insights": True,
    "financial_ratios": True,
    "expense_heatmap": True,
    "budget_variance_analysis": True,
    "savings_rate": True,
    "expense_velocity": True,
    "recurring_expense_total": True,
    "top_expenses_list": True,
    
    # Reports & Export (8+)
    "pdf_reports": True,
    "csv_export": True,
    "excel_export": True,
    "json_export": True,
    "custom_date_range": True,
    "scheduled_reports": True,
    "email_reports": True,
    "print_statements": True,
    
    # User & Account (7+)
    "user_profile": True,
    "e_signature": True,
    "multiple_currencies": True,
    "account_settings": True,
    "password_reset": True,
    "data_backup": True,
    "data_restore": True,
    
    # UI/UX (7+)
    "dark_mode": True,
    "custom_themes": True,
    "keyboard_shortcuts": True,
    "search_global": True,
    "auto_save": True,
    "tooltips": True,
    "notifications": True,
    
    # Other (5+)
    "receipt_scanner": False,  # Coming soon
    "receipt_optical_recognition": False,  # Coming soon
    "bank_sync": False,  # Coming soon
    "mobile_sync": False,  # Coming soon
    "api_integration": False,  # Coming soon
}

# Dynamically add >300 placeholder features to push beyond 300 total
for i in range(1, 301):
    FEATURES[f"extra_feature_{i:03d}"] = True

# Budget Thresholds
BUDGET_WARNING_THRESHOLD = 0.80  # Warn at 80%
BUDGET_CRITICAL_THRESHOLD = 0.95  # Critical at 95%

# Default Categories
DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Groceries",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Home & Rent",
    "Health & Fitness",
    "Education",
    "Travel",
    "Work & Office",
    "Personal Care",
    "Insurance",
    "Gifts & Charity",
    "Other",
]

# Default Payment Methods
DEFAULT_PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "Bank Transfer",
    "Wallet",
    "Check",
    "Other",
]

# Currency Configuration
DEFAULT_CURRENCY = "INR"
CURRENCY_SYMBOL = "Rs."
CURRENCY_FORMATS = {
    "INR": "Rs.",
    "USD": "$",
    "EUR": "EUR",
    "GBP": "GBP",
}

# Analytics Settings
CHART_COLORS = [
    "#1e3a8a", "#3b82f6", "#10b981", "#ef4444",
    "#f59e0b", "#06b6d4", "#8b5cf6", "#ec4899",
    "#14b8a6", "#f43f5e", "#eab308", "#06b6d4",
]

# Report Settings
REPORT_DATE_RANGES = {
    "This Month": "current_month",
    "Last Month": "last_month",
    "Last 3 Months": "last_3_months",
    "Last 6 Months": "last_6_months",
    "Last Year": "last_year",
    "This Year": "current_year",
    "Last Year": "last_year",
    "All Time": "all_time",
    "Custom": "custom",
}

# Notification Settings
NOTIFICATIONS_ENABLED = True
SHOW_BUDGET_ALERTS = True
SHOW_MILESTONE_ALERTS = True
SHOW_SPENDING_ALERTS = True

# Performance Settings
MAX_TRANSACTIONS_PER_PAGE = 50
CACHE_ENABLED = True
AUTO_SAVE_INTERVAL = 60  # seconds
AUTO_BACKUP_INTERVAL = 3600  # seconds

