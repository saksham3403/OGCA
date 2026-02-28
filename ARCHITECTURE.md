# Expense Tracker Pro - Architecture Overview

## Application Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py (Entry Point)                     │
│                    (Launches Application)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Start UI   │
                    │  Selection  │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │                     │
        ┌───────▼────────┐    ┌───────▼────────┐
        │ First Time?    │    │ Existing User? │
        │  (No Account)  │    │ (Has Account)  │
        └───────┬────────┘    └───────┬────────┘
                │                     │
        ┌───────▼──────┐      ┌───────▼──────┐
        │ auth_ui.py   │      │ auth_ui.py   │
        │  Register    │      │   Login      │
        │  Form        │      │   Form       │
        └───────┬──────┘      └───────┬──────┘
                │                     │
        ┌───────▼──────┐      ┌───────▼──────┐
        │ database.py  │      │ database.py  │
        │ register_user│      │ login_user   │
        └───────┬──────┘      └───────┬──────┘
                │                     │
                └──────────┬──────────┘
                           │
                    ┌──────▼──────────┐
                    │ expense_tracker │
                    │ MainApplication │
                    │      UI         │
                    └──────┬──────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
     │ Dashboard │  │Transaction│  │  Reports  │
     │  (Stats)  │  │  Manager  │  │  (PDF)    │
     └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
           │               │              │
           │        ┌──────┼──────┐      │
           │        │             │      │
     ┌─────▼─┐  ┌───▼──┐  ┌──────▼──┐   │
     │database│  │Expenses│ │Income│ │   │
     │queries │  │  (Add)  │ │(Add) │ │   │
     └────────┘  └────────┘ └───────┘   │
                                        │
                 ┌──────────────────────▼────────┐
                 │  pdf_generator.py             │
                 │  - Expense Reports           │
                 │  - Balance Sheets            │
                 │  - Professional Format      │
                 │  - E-Signature Support      │
                 └───────┬─────────────────────┘
                         │
                    ┌────▼────┐
                    │  PDF    │
                    │  File   │
                    └─────────┘
```

---

## Module Interaction Diagram

```
┌────────────────────────────────────────────────────────────┐
│                  config.py                                  │
│  (Constants, Colors, Fonts, Paths - Used by all modules)   │
└────────────────────────────────────────────────────────────┘
                          ▲
                          │ (imports)
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌───▼────┐      ┌───▼────┐
    │utils.py │      │auth_ui │      │database│
    │(Widgets)│      │(Forms) │      │(Models)│
    │(Helpers)│      │        │      │        │
    └────┬────┘      └───┬────┘      └───┬────┘
         │               │               │
         │ ┌─────────────┼───────────────┤
         │ │             │               │
         │ │       ┌─────▼────────┐     │
         │ └──────▶│ main.py      │◀────┘
         │         │(Entry Point) │
         │         └─────┬────────┘
         │               │
         │         ┌─────▼──────────────┐
         └────────▶│expense_tracker.py  │
                   │ (Main Application) │
                   └─────┬──────────────┘
                         │
                    ┌────▼─────────────┐
                    │pdf_generator.py  │
                    │(Report Creator)  │
                    └──────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                 User Input                               │
│  - Login/Register form                                   │
│  - Transaction entry                                     │
│  - Profile update                                        │
└─────────────────┬───────────────────────────────────────┘
                  │
            ┌─────▼──────┐
            │ utils.py   │
            │Validation  │
            │& Formatting│
            └─────┬──────┘
                  │
            ┌─────▼────────────┐
            │  database.py     │
            │  - CRUD Ops      │
            │  - Queries       │
            │  - Calculations  │
            └─────┬────────────┘
                  │
            ┌─────▼─────────┐
            │  SQLite DB    │
            │ (Persistent   │
            │  Storage)     │
            └─────┬─────────┘
                  │
       ┌──────────┼──────────┐
       │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌──▼────┐
  │ Users  │ │Expenses│ │Income  │
  │ Table  │ │ Table  │ │ Table  │
  └────┬───┘ └───┬────┘ └──┬────┘
       │         │         │
       └──────────┼─────────┘
                  │
            ┌─────▼──────────┐
            │  Show Results  │
            │ - Dashboard    │
            │ - Reports      │
            │ - PDF Export   │
            └────────────────┘
```

---

## UI Component Hierarchy

```
┌──────────────────────────────────┐
│         Main Window              │
│        (1200x700)                │
└──────────────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
   ┌────▼─────┐    ┌───▼────┐
   │Navigation│    │Content  │
   │ Bar      │    │ Area    │
   │(Top)     │    │         │
   └────┬─────┘    └───┬────┘
        │              │
   ┌────▼─────┐    ┌───▼─────────────┐
   │Logo      │    │Dashboard/       │
   │Buttons   │    │Transactions/    │
   │User Info │    │Reports/Profile  │
   │Logout    │    │(Tabbed/Stacked) │
   └──────────┘    └────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
   ┌────▼────┐      ┌────▼────┐      ┌─────▼────┐
   │ Forms   │      │ Tables  │      │ Cards/   │
   │ (Input) │      │ (List)  │      │ Stats    │
   └─────────┘      └─────────┘      └──────────┘
```

---

## Feature Tree

```
Expense Tracker Pro
│
├── Authentication
│   ├── User Registration
│   │   └── Form Validation
│   └── User Login
│       └── Password Verification
│
├── Dashboard
│   ├── Financial Summary
│   │   ├── Total Income
│   │   ├── Total Expenses
│   │   └── Balance
│   ├── Recent Transactions
│   └── Category Breakdown
│
├── Transactions
│   ├── Expenses Management
│   │   ├── Add Expense
│   │   ├── View Expenses
│   │   ├── Edit Expense
│   │   └── Delete Expense
│   └── Income Management
│       ├── Add Income
│       ├── View Income
│       ├── Edit Income
│       └── Delete Income
│
├── Reports
│   ├── Expense Reports
│   │   ├── Monthly Export
│   │   ├── Quarterly Export
│   │   └── Yearly Export
│   └── Balance Sheets
│       ├── Income Analysis
│       ├── Expense Analysis
│       └── Financial Metrics
│
├── PDF Generation
│   ├── Professional Formatting
│   ├── Company Information
│   ├── Financial Tables
│   ├── Category Breakdown
│   └── E-Signature Section
│
└── Profile Management
    ├── Personal Information
    ├── Contact Details
    └── E-Signature
```

---

## Database Relationship Diagram

```
┌──────────────────┐
│    users         │
├──────────────────┤
│ id (PK)          │
│ username (U)     │
│ email (U)        │
│ password_hash    │
│ salt             │
│ full_name        │
│ phone            │
│ address          │
│ city             │
│ state            │
│ zip_code         │
│ e_signature      │
│ timestamps       │
└────────┬─────────┘
         │ (1:M)
         │
    ┌────┴────────────────┬──────────────────┐
    │                     │                  │
    │ (1:M)         (1:M) │            (1:M) │
    │                     │                  │
┌───▼──────────┐  ┌──────▼───────┐  ┌──────▼────┐
│  expenses    │  │   income     │  │  budgets  │
├──────────────┤  ├──────────────┤  ├───────────┤
│ id (PK)      │  │ id (PK)      │  │ id (PK)   │
│ user_id (FK) │  │ user_id (FK) │  │ user_id(FK)
│ category     │  │ source       │  │ category  │
│ amount       │  │ amount       │  │ limit_amt │
│ date         │  │ date         │  │ month     │
│ description  │  │ description  │  │ year      │
│ payment_meth │  │ notes        │  │ timestamps│
│ notes        │  │ timestamps   │  └───────────┘
│ timestamps   │  │              │
└──────────────┘  └──────────────┘

         (Many users have Many categories)
                    │
         ┌──────────▼───────────┐
         │    categories        │
         ├──────────────────────┤
         │ id (PK)              │
         │ user_id (FK)         │
         │ name                 │
         │ type                 │
         │ color                │
         │ icon                 │
         │ created_at           │
         └──────────────────────┘
```

---

## File Size & Complexity

| File | Lines | Complexity | Purpose |
|------|-------|-----------|---------|
| main.py | ~50 | Low | Entry point |
| config.py | ~80 | Low | Configuration |
| utils.py | ~200 | Low-Medium | Utilities |
| auth_ui.py | ~400 | Medium | Authentication |
| database.py | ~450 | Medium | Database layer |
| expense_tracker.py | ~800 | High | Main UI |
| pdf_generator.py | ~550 | High | PDF generation |
| **Total** | **~2,530** | - | - |

---

## Deployment Architecture

```
┌──────────────────────────────────────┐
│        Windows/Mac/Linux             │
│       (User's Computer)              │
└──────────────────────────────────────┘
                 │
    ┌────────────▼────────────┐
    │   Python Runtime 3.7+   │
    ├────────────────────────┤
    │ • tkinter (Built-in)   │
    │ • sqlite3 (Built-in)   │
    │ • reportlab (4.0.7)    │
    │ • Pillow (10.1.0)      │
    │ • dateutil (2.8.2)     │
    └────────────┬───────────┘
                 │
    ┌────────────▼────────────┐
    │  Expense Tracker App    │
    ├────────────────────────┤
    │ • main.py              │
    │ • expense_tracker.py   │
    │ • auth_ui.py           │
    │ • pdf_generator.py     │
    │ • database.py          │
    │ • utils.py             │
    │ • config.py            │
    └────────────┬───────────┘
                 │
    ┌────────────▼────────────┐
    │       SQLite DB         │
    │ (expense_tracker.db)    │
    └────────────────────────┘
```

---

## Security Architecture

```
User Input
    │
    ▼
┌─────────────────────┐
│ Input Validation    │
│ - Email format      │
│ - Password strength │
│ - Amount format     │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Sanitization        │
│ - SQL injection     │
│ - XSS prevention    │
│ - Type checking     │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Authentication      │
│ - PBKDF2-SHA256     │
│ - 100K iterations   │
│ - 32-byte salt      │
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Database Storage    │
│ - Foreign keys      │
│ - Constraints       │
│ - Transactions      │
└─────────────────────┘
```

---

**Architecture Last Updated**: February 26, 2026

This comprehensive architecture ensures scalability, security, and maintainability of the Expense Tracker Pro application.
