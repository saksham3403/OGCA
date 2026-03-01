# QUICK START GUIDE - Expense Tracker Pro

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application
```bash
python main.py
```

### Step 3: Create Your Account & Start Tracking!

---

## 📋 First Time Setup

### Test Account (Optional)
1. Click "Create one" to register
2. Fill in your details:
   - **Full Name**: Your Name
   - **Username**: testuser123
   - **Email**: your@email.com
   - **Password**: Password123 (must have: 6+ chars, 1 uppercase, 1 number)
3. Click "Create Account"
4. Login with your credentials

---

## 💡 Key Features to Explore

### 1. **Dashboard**
- View your total income, expenses, and balance
- See recent transactions
- Check category breakdown of spending

### 2. **Transactions**
- **Add Expenses**: Track spending by category
  - Categories: Food, Transport, Entertainment, Utilities, Healthcare, Education, Other
  - Supported payment methods: Cash, Card, UPI, Other
- **Add Income**: Record income sources
  - Track salary, freelance, investments, etc.

### 3. **Reports** ⭐
- **Expense Report**: Export PDF for Month/Quarter/Year
  - Includes detailed transaction list
  - Category breakdown with percentages
  - Financial summary
- **Balance Sheet**: Professional accounting format
  - Income vs Expenses analysis
  - Financial metrics (Profit Margin, Expense Ratio)
  - Authorized signature section

### 4. **Profile**
- Update personal information
- Add address and contact details
- Manage e-signature for PDF documents

---

## 📊 Sample Data to Add

### Add Expense Example:
- Category: Food
- Amount: 500.00
- Date: 2024-02-20
- Description: Lunch at office
- Payment Method: Card

### Add Income Example:
- Source: Salary
- Amount: 50000.00
- Date: 2024-02-20
- Description: Monthly salary

---

## 🎯 Generate Your First Report

1. Go to **Reports** tab
2. Click "Export Month" under Expense Report
3. Choose save location
4. Open the PDF to see:
   - Professional accounting format
   - Your name and contact info
   - Transaction details
   - Financial analysis
   - Signature section

---

## 🔐 Password Requirements

Your password must have:
- ✅ At least 6 characters
- ✅ At least 1 UPPERCASE letter
- ✅ At least 1 digit (0-9)

Example valid passwords:
- `MyPass123`
- `Secure@2024`
- `Finance#Tracker1`

---

## 🗂️ Project Files Explained

| File | Purpose |
|------|---------|
| `main.py` | Application entry point - Run this file! |
| `config.py` | Settings, colors, fonts, constants |
| `database.py` | SQLite database operations |
| `auth_ui.py` | Login & Registration screens |
| `expense_tracker.py` | Main application interface |
| `pdf_generator.py` | Professional PDF report generation |
| `utils.py` | Reusable UI components & functions |

---

## 📱 Application Layout

```
┌─────────────────────────────────────────┐
│  💰 Expense Tracker │ Menu Buttons │ Logout
├─────────────────────────────────────────┤
│                                         │
│           Main Content Area             │
│                                         │
│  Dashboard / Transactions / Reports     │
│                                         │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Problem: "Module not found" error
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Problem: Window won't display
```bash
# Solution: Make sure tkinter is installed
# The following should be available in Python 3.7+
import tkinter
```

### Problem: Reports not generating
- Ensure there's at least one transaction
- Check that the save location is writable
- Verify pdf_generator.py is in the same folder

---

## 📈 Tips for Best Use

✨ **Track Regularly**: Add transactions daily for accurate reports

💼 **Categorize Properly**: Use consistent categories for better analysis

📊 **Review Reports**: Generate monthly reports to identify spending patterns

💰 **Set Budgets**: Monitor your spending to stay within limits

🔐 **Secure Your Account**: Use a strong password

---

## 🎓 Advanced Features

- **Export to PDF**: All reports are in professional accounting format
- **E-Signature**: Add your signature to official documents  
- **Financial Analytics**: View profit margins and expense ratios
- **Category Analysis**: See where your money goes
- **Balance Sheets**: Professional financial statements

---

## 📞 Need Help?

Check the README.md for detailed documentation

---

**Version**: 1.0.0  
**Last Updated**: February 26, 2026

🎉 **Happy Tracking!**
