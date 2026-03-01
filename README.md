# Expense Tracker Pro

A professional, full-featured expense tracking application built with Python tkinter. Features advanced UI/UX design, user authentication, PDF reporting in accounting format, and balance sheet generation.

## Features

✨ **Core Features**
- 👤 User Authentication (Login & Register with password hashing)
- 💰 Track Income and Expenses with categories
- 📊 Real-time Financial Dashboard
- 💼 Professional Accounting-Style PDF Reports
- 📈 Balance Sheet Generation
- 📋 Transaction History & Management
- 🎯 Budget Planning (Coming Soon)

✨ **Advanced Features**
- Beautiful, modern UI with consistent design
- SQLite database for secure data storage
- Category-wise expense breakdown with analytics
- Multiple payment method tracking
- Detailed transaction notes
- Date-based filtering and reporting
- E-signature support on PDF documents
- Responsive design

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or Download the Project**
   ```bash
   cd "c:\Users\sakshxmsingh\Desktop\tkinter programs"
   ```

2. **Install Required Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   The following packages will be installed:
   - `reportlab==4.0.7` - For PDF generation
   - `pillow==10.1.0` - For image handling
   - `python-dateutil==2.8.2` - For date utilities

3. **Run the Application**
   ```bash
   python main.py
   ```

## Project Structure

```
tkinter programs/
├── main.py                 # Application entry point
├── config.py              # Configuration & constants
├── database.py            # Database operations & models
├── auth_ui.py            # Login & Registration UI
├── expense_tracker.py    # Main application UI
├── pdf_generator.py      # PDF report generation
├── utils.py              # Utility functions & custom widgets
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Usage

### Getting Started

1. **Launch the Application**
   ```bash
   python main.py
   ```

2. **Create an Account**
   - Click "Create one" on the login screen
   - Fill in all required fields
   - Password must contain: 6+ chars, 1 uppercase, 1 digit
   - Click "Create Account"

3. **Login**
   - Enter your username and password
   - Click "Sign In"

### Using the Dashboard

**Dashboard Tab:**
- View your financial summary (Total Income, Expenses, Balance)
- See recent transactions
- View expenses by category

**Transactions Tab:**
- **Expenses**: Add income entries with category, amount, date, and payment method
- **Income**: Add income sources with amount and date
- View complete transaction history

**Reports Tab:**
- **Expense Reports**: Export detailed expense reports for Month, Quarter, or Year
- **Balance Sheet**: Generate professional balance sheet in accounting format

**Profile Tab:**
- Update personal information
- Manage contact details
- Save profile changes

## Password Requirements

- Minimum 6 characters
- At least 1 uppercase letter (A-Z)
- At least 1 digit (0-9)

## Database

The application uses SQLite for data storage. A database file (`expense_tracker.db`) is automatically created on first run.

### Database Tables:
- `users` - User accounts with authentication
- `expenses` - Expense records
- `income` - Income records
- `budgets` - Budget tracking
- `categories` - Custom expense categories
- `transaction_archive` - Archived transactions

## PDF Report Format

PDF reports are generated in professional accounting format with:
- Company/Personal Information Header
- Financial Summary Tables
- Detailed Transaction Lists
- Category Breakdown Analysis
- Financial Metrics (Profit Margin, Expense Ratio, etc.)
- E-Signature Section
- Professional accounting layout

## Security Features

✅ **Passwords**
- Hashed with PBKDF2-SHA256
- Salt-based encryption
- 100,000 iterations for security

✅ **Data Protection**
- SQLite database with foreign key support
- Input validation and sanitization
- Secure user session management

## Color Scheme

- **Primary Blue**: #1e3a8a
- **Success Green**: #10b981
- **Danger Red**: #ef4444
- **Warning Amber**: #f59e0b
- **Light Background**: #f9fafb

## Font Family

Uses "Segoe UI" for modern, clean typography with fallback fonts.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'reportlab'"
**Solution**: Run `pip install -r requirements.txt`

### Issue: Database file not found
**Solution**: Delete `expense_tracker.db` if corrupted. The app will create a new one.

### Issue: Window doesn't display properly
**Solution**: Ensure your Python tkinter is properly installed:
```bash
# Windows
python -m pip install tk

# Linux
sudo apt-get install python3-tk
```

## Future Enhancements

- 📱 Mobile application version
- ☁️ Cloud synchronization
- 📊 Advanced analytics & charts
- 💳 Bank account integration
- 🔐 Two-factor authentication
- � Receipt scanning with OCR
- 🤖 AI-powered spending recommendations
- 📲 Mobile notification alerts

## License

This project is open source and available under the MIT License.

## Support

For issues, feature requests, or contributions, please contact the development team.

## Version

Current Version: 1.0.0
Last Updated: February 26, 2026

---

Made with ❤️ for better financial management
