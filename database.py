"""Database module for Expense Tracker"""
import sqlite3
import hashlib
import os
import json
from datetime import datetime
from config import DB_PATH, SALT_LENGTH


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database with tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                e_signature BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                payment_method TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Income table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Budget table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                limit_amount REAL NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Recurring bills table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                frequency TEXT NOT NULL,
                start_date DATE NOT NULL,
                next_due_date DATE NOT NULL,
                payment_method TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                last_run_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                color TEXT,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, name)
            )
        ''')

        # Managed Accounts (People Accounts)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managed_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                city TEXT,
                notes TEXT,
                color TEXT,
                icon TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, account_name)
            )
        ''')

        # Transaction archive
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                transaction_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Trash bin for recoverable deletes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trash_bin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                item_data TEXT NOT NULL,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Subscriptions center
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                billing_cycle TEXT NOT NULL,
                next_billing_date DATE NOT NULL,
                category TEXT DEFAULT 'Utilities',
                status TEXT DEFAULT 'active',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Report designer preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_design_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                brand_name TEXT,
                primary_color TEXT,
                footer_note TEXT,
                layout_mode TEXT DEFAULT 'standard',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Statement import rules (merchant keyword -> category/account mapping)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                category TEXT NOT NULL,
                account_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Financial goals tracker
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                due_date DATE,
                category TEXT DEFAULT 'General',
                notes TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # In-app notification center
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'info',
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Quick notes workspace
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                body TEXT DEFAULT '',
                color_tag TEXT DEFAULT 'blue',
                is_pinned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Reminders planner
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date DATE NOT NULL,
                priority TEXT DEFAULT 'medium',
                note TEXT DEFAULT '',
                is_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # Add account_id column to expenses if not exists
        try:
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'account_id' not in columns:
                cursor.execute('ALTER TABLE expenses ADD COLUMN account_id INTEGER DEFAULT NULL')
        except Exception as e:
            pass

        # Add account_id column to income if not exists
        try:
            cursor.execute("PRAGMA table_info(income)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'account_id' not in columns:
                cursor.execute('ALTER TABLE income ADD COLUMN account_id INTEGER DEFAULT NULL')
        except Exception as e:
            pass

        # Add attachment_path column to expenses if not exists
        try:
            cursor.execute("PRAGMA table_info(expenses)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'attachment_path' not in columns:
                cursor.execute('ALTER TABLE expenses ADD COLUMN attachment_path TEXT DEFAULT NULL')
        except Exception:
            pass

        conn.commit()
        conn.close()

    @staticmethod
    def hash_password(password):
        """Hash password with salt"""
        salt = os.urandom(SALT_LENGTH).hex()
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hashed, salt

    @staticmethod
    def verify_password(password, salt, hashed):
        """Verify password"""
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return new_hash == hashed

    # User operations
    def register_user(self, username, email, password, full_name=""):
        """Register a new user"""
        try:
            hashed, salt = self.hash_password(password)
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, salt, full_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed, salt, full_name))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError as e:
            return None

    def login_user(self, username, password):
        """Login user and return user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and self.verify_password(password, user['salt'], user['password_hash']):
            return dict(user)
        return None

    def get_user(self, user_id):
        """Get user data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    def update_user(self, user_id, **kwargs):
        """Update user information"""
        allowed_fields = {'full_name', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'e_signature'}
        fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [user_id]
        
        cursor.execute(f'''
            UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        return True

    def get_all_users(self, search_text=""):
        """Return all users for admin/user-management views."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if search_text:
            like = f"%{search_text.strip()}%"
            cursor.execute(
                '''
                SELECT id, username, email, full_name, phone, city, state, created_at, updated_at
                FROM users
                WHERE username LIKE ? OR email LIKE ? OR full_name LIKE ?
                ORDER BY id ASC
                ''',
                (like, like, like)
            )
        else:
            cursor.execute(
                '''
                SELECT id, username, email, full_name, phone, city, state, created_at, updated_at
                FROM users
                ORDER BY id ASC
                '''
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def update_user_admin(self, user_id, **kwargs):
        """Admin-level user update including username/email and profile fields."""
        allowed_fields = {
            'username', 'email', 'full_name', 'phone',
            'address', 'city', 'state', 'zip_code'
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not fields:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [user_id]
        try:
            cursor.execute(
                f'''
                UPDATE users
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                values
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def update_user_password(self, user_id, new_password):
        """Update user password with fresh salt/hash."""
        hashed, salt = self.hash_password(new_password)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE users
            SET password_hash = ?, salt = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (hashed, salt, user_id)
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_user(self, user_id):
        """Delete user by id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # Expense operations
    def add_expense(self, user_id, category, amount, date, description="", payment_method="", notes="", account_id=None, attachment_path=None):
        """Add expense"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if account_id:
            cursor.execute('''
                INSERT INTO expenses (user_id, account_id, category, amount, date, description, payment_method, notes, attachment_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, account_id, category, amount, date, description, payment_method, notes, attachment_path))
        else:
            cursor.execute('''
                INSERT INTO expenses (user_id, category, amount, date, description, payment_method, notes, attachment_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, category, amount, date, description, payment_method, notes, attachment_path))
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        return expense_id

    def get_expenses(self, user_id, start_date=None, end_date=None):
        """Get user expenses"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM expenses 
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (user_id,))
        
        expenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return expenses

    def update_expense(self, expense_id, **kwargs):
        """Update expense"""
        allowed_fields = {'category', 'amount', 'date', 'description', 'payment_method', 'notes', 'attachment_path'}
        fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [expense_id]
        
        cursor.execute(f'''
            UPDATE expenses SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        return True

    def delete_expense(self, expense_id):
        """Delete expense"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()

    # Income operations
    def add_income(self, user_id, source, amount, date, description="", notes="", account_id=None):
        """Add income"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if account_id:
            cursor.execute('''
                INSERT INTO income (user_id, account_id, source, amount, date, description, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, account_id, source, amount, date, description, notes))
        else:
            cursor.execute('''
                INSERT INTO income (user_id, source, amount, date, description, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, source, amount, date, description, notes))
        conn.commit()
        income_id = cursor.lastrowid
        conn.close()
        return income_id

    def get_income(self, user_id, start_date=None, end_date=None):
        """Get user income"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM income 
                WHERE user_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (user_id, start_date, end_date))
        else:
            cursor.execute('SELECT * FROM income WHERE user_id = ? ORDER BY date DESC', (user_id,))
        
        income = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return income

    def update_income(self, income_id, **kwargs):
        """Update income"""
        allowed_fields = {'source', 'amount', 'date', 'description', 'notes'}
        fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not fields:
            return False

        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [income_id]
        
        cursor.execute(f'''
            UPDATE income SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
        return True

    def delete_income(self, income_id):
        """Delete income"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM income WHERE id = ?', (income_id,))
        conn.commit()
        conn.close()

    # Trash bin
    def trash_item(self, user_id, item_type, item_data):
        """Move item snapshot into trash bin."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO trash_bin (user_id, item_type, item_data)
            VALUES (?, ?, ?)
            ''',
            (user_id, item_type, json.dumps(item_data))
        )
        conn.commit()
        trash_id = cursor.lastrowid
        conn.close()
        return trash_id

    def get_trash_items(self, user_id):
        """List trashed items for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT * FROM trash_bin
            WHERE user_id = ?
            ORDER BY deleted_at DESC
            ''',
            (user_id,)
        )
        rows = []
        for row in cursor.fetchall():
            d = dict(row)
            try:
                d["item_data"] = json.loads(d["item_data"])
            except Exception:
                d["item_data"] = {}
            rows.append(d)
        conn.close()
        return rows

    def restore_trash_item(self, trash_id, user_id):
        """Restore one trashed expense/income item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM trash_bin WHERE id = ? AND user_id = ?', (trash_id, user_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Trash item not found"

        data = json.loads(row["item_data"])
        item_type = row["item_type"]
        try:
            if item_type == "expense":
                cursor.execute(
                    '''
                    INSERT INTO expenses (user_id, account_id, category, amount, date, description, payment_method, notes, attachment_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        user_id,
                        data.get("account_id"),
                        data.get("category", "Other"),
                        data.get("amount", 0),
                        data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        data.get("description", ""),
                        data.get("payment_method", ""),
                        data.get("notes", ""),
                        data.get("attachment_path"),
                    )
                )
            elif item_type == "income":
                cursor.execute(
                    '''
                    INSERT INTO income (user_id, account_id, source, amount, date, description, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        user_id,
                        data.get("account_id"),
                        data.get("source", "Other"),
                        data.get("amount", 0),
                        data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        data.get("description", ""),
                        data.get("notes", ""),
                    )
                )
            else:
                conn.close()
                return False, "Unsupported trash item type"

            cursor.execute('DELETE FROM trash_bin WHERE id = ? AND user_id = ?', (trash_id, user_id))
            conn.commit()
            conn.close()
            return True, "Restored"
        except Exception as e:
            conn.close()
            return False, str(e)

    def delete_trash_item(self, trash_id, user_id):
        """Permanently delete one trash item."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trash_bin WHERE id = ? AND user_id = ?', (trash_id, user_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    # Subscriptions
    def add_subscription(self, user_id, name, amount, billing_cycle, next_billing_date, category="Utilities", notes=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO subscriptions (user_id, name, amount, billing_cycle, next_billing_date, category, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (user_id, name, amount, billing_cycle, next_billing_date, category, notes)
        )
        conn.commit()
        sub_id = cursor.lastrowid
        conn.close()
        return sub_id

    def get_subscriptions(self, user_id, active_only=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY next_billing_date",
                (user_id,)
            )
        else:
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY next_billing_date",
                (user_id,)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_subscription(self, subscription_id, user_id, **kwargs):
        allowed = {"name", "amount", "billing_cycle", "next_billing_date", "category", "status", "notes"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [subscription_id, user_id]
        cursor.execute(
            f'''
            UPDATE subscriptions
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    def delete_subscription(self, subscription_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM subscriptions WHERE id = ? AND user_id = ?', (subscription_id, user_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    def get_subscription_summary(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COUNT(*) as total_count, COALESCE(SUM(amount), 0) as total_amount
            FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ''',
            (user_id,)
        )
        row = dict(cursor.fetchone())
        conn.close()
        return row

    # Report design settings
    def set_report_design(self, user_id, brand_name, primary_color, footer_note, layout_mode="standard"):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM report_design_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            cursor.execute(
                '''
                UPDATE report_design_settings
                SET brand_name = ?, primary_color = ?, footer_note = ?, layout_mode = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                ''',
                (brand_name, primary_color, footer_note, layout_mode, user_id)
            )
        else:
            cursor.execute(
                '''
                INSERT INTO report_design_settings (user_id, brand_name, primary_color, footer_note, layout_mode)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, brand_name, primary_color, footer_note, layout_mode)
            )
        conn.commit()
        conn.close()
        return True

    def get_report_design(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM report_design_settings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # Budget operations
    def add_budget(self, user_id, category, limit_amount, month, year):
        """Add budget"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO budgets (user_id, category, limit_amount, month, year)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, category, limit_amount, month, year))
        conn.commit()
        budget_id = cursor.lastrowid
        conn.close()
        return budget_id

    def get_budgets(self, user_id, month=None, year=None):
        """Get user budgets"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if month and year:
            cursor.execute('''
                SELECT * FROM budgets 
                WHERE user_id = ? AND month = ? AND year = ?
            ''', (user_id, month, year))
        else:
            cursor.execute('SELECT * FROM budgets WHERE user_id = ?', (user_id,))
        
        budgets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return budgets

    def add_or_update_budget(self, user_id, category, limit_amount, month, year):
        """Create or update budget for month/category."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id FROM budgets
            WHERE user_id = ? AND category = ? AND month = ? AND year = ?
            ''',
            (user_id, category, month, year)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                '''
                UPDATE budgets
                SET limit_amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                ''',
                (limit_amount, row["id"])
            )
            budget_id = row["id"]
        else:
            cursor.execute(
                '''
                INSERT INTO budgets (user_id, category, limit_amount, month, year)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (user_id, category, limit_amount, month, year)
            )
            budget_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return budget_id

    def delete_budget(self, budget_id, user_id):
        """Delete one budget row."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM budgets WHERE id = ? AND user_id = ?', (budget_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_budget_vs_actual(self, user_id, month, year):
        """Get budget vs actual spending for a month."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT category, limit_amount
            FROM budgets
            WHERE user_id = ? AND month = ? AND year = ?
            ORDER BY category
            ''',
            (user_id, month, year)
        )
        budgets = [dict(row) for row in cursor.fetchall()]
        result = []
        for b in budgets:
            cursor.execute(
                '''
                SELECT COALESCE(SUM(amount), 0) as spent
                FROM expenses
                WHERE user_id = ? AND category = ?
                  AND strftime('%m', date) = ?
                  AND strftime('%Y', date) = ?
                ''',
                (user_id, b["category"], f"{int(month):02d}", str(year))
            )
            spent = float(cursor.fetchone()["spent"] or 0)
            limit_amount = float(b["limit_amount"])
            result.append({
                "category": b["category"],
                "limit_amount": limit_amount,
                "spent": spent,
                "remaining": limit_amount - spent,
                "usage_percent": (spent / limit_amount * 100) if limit_amount > 0 else 0,
            })
        conn.close()
        return result

    # Recurring bill operations
    def add_recurring_bill(
        self,
        user_id,
        title,
        category,
        amount,
        frequency,
        start_date,
        payment_method="",
        description="",
        is_active=1,
    ):
        """Add recurring bill rule."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO recurring_bills
            (user_id, title, category, amount, frequency, start_date, next_due_date, payment_method, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id,
                title,
                category,
                amount,
                frequency,
                start_date,
                start_date,
                payment_method,
                description,
                int(is_active),
            )
        )
        conn.commit()
        bill_id = cursor.lastrowid
        conn.close()
        return bill_id

    def get_recurring_bills(self, user_id, active_only=False):
        """Get recurring bills."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute(
                'SELECT * FROM recurring_bills WHERE user_id = ? AND is_active = 1 ORDER BY next_due_date',
                (user_id,)
            )
        else:
            cursor.execute(
                'SELECT * FROM recurring_bills WHERE user_id = ? ORDER BY next_due_date',
                (user_id,)
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def update_recurring_bill(self, bill_id, user_id, **kwargs):
        """Update recurring bill fields."""
        allowed = {
            "title", "category", "amount", "frequency", "start_date",
            "next_due_date", "payment_method", "description", "is_active", "last_run_at"
        }
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [bill_id, user_id]
        cursor.execute(
            f'''
            UPDATE recurring_bills
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    def delete_recurring_bill(self, bill_id, user_id):
        """Delete recurring bill."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM recurring_bills WHERE id = ? AND user_id = ?', (bill_id, user_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    @staticmethod
    def _next_due_date(current_date_str, frequency):
        """Compute next due date from a date + frequency."""
        from datetime import datetime, timedelta
        current = datetime.strptime(current_date_str, "%Y-%m-%d")
        freq = (frequency or "").lower().strip()
        if freq == "weekly":
            nxt = current + timedelta(days=7)
        elif freq == "quarterly":
            nxt = current + timedelta(days=90)
        elif freq == "yearly":
            nxt = current + timedelta(days=365)
        else:
            nxt = current + timedelta(days=30)  # monthly default
        return nxt.strftime("%Y-%m-%d")

    def run_due_recurring_bills(self, user_id, run_date=None):
        """Create expenses for recurring bills due on/before run_date."""
        from datetime import datetime
        run_date = run_date or datetime.now().strftime("%Y-%m-%d")
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT * FROM recurring_bills
            WHERE user_id = ? AND is_active = 1 AND next_due_date <= ?
            ORDER BY next_due_date
            ''',
            (user_id, run_date)
        )
        due_bills = [dict(row) for row in cursor.fetchall()]
        created = 0
        for bill in due_bills:
            note = f"[Auto Recurring] {bill.get('title', '')}".strip()
            cursor.execute(
                '''
                INSERT INTO expenses (user_id, category, amount, date, description, payment_method, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    bill["category"],
                    bill["amount"],
                    bill["next_due_date"],
                    bill.get("description", "") or bill.get("title", ""),
                    bill.get("payment_method", ""),
                    note,
                )
            )
            next_due = self._next_due_date(bill["next_due_date"], bill["frequency"])
            cursor.execute(
                '''
                UPDATE recurring_bills
                SET next_due_date = ?, last_run_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                ''',
                (next_due, bill["id"], user_id)
            )
            created += 1
        conn.commit()
        conn.close()
        return created

    def suggest_category(self, user_id, description):
        """Suggest most likely category based on historical descriptions."""
        if not description:
            return None
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT category, COUNT(*) as cnt
            FROM expenses
            WHERE user_id = ? AND description IS NOT NULL AND LOWER(description) LIKE ?
            GROUP BY category
            ORDER BY cnt DESC
            LIMIT 1
            ''',
            (user_id, f"%{description.lower()}%")
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return row["category"]
        return None

    def statement_txn_exists(self, user_id, txn_id):
        """Check whether a statement transaction id is already imported."""
        if not txn_id:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        marker = f"%[STATEMENT:{txn_id}]%"
        cursor.execute(
            '''
            SELECT 1 FROM expenses WHERE user_id = ? AND notes LIKE ?
            UNION
            SELECT 1 FROM income WHERE user_id = ? AND notes LIKE ?
            LIMIT 1
            ''',
            (user_id, marker, user_id, marker)
        )
        row = cursor.fetchone()
        conn.close()
        return bool(row)

    # Import rules
    def add_import_rule(self, user_id, keyword, category, account_name=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO import_rules (user_id, keyword, category, account_name)
            VALUES (?, ?, ?, ?)
            ''',
            (user_id, keyword.strip().lower(), category.strip(), account_name.strip())
        )
        conn.commit()
        rid = cursor.lastrowid
        conn.close()
        return rid

    def get_import_rules(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT * FROM import_rules
            WHERE user_id = ?
            ORDER BY LENGTH(keyword) DESC, id DESC
            ''',
            (user_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def delete_import_rule(self, rule_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM import_rules WHERE id = ? AND user_id = ?', (rule_id, user_id))
        conn.commit()
        ok = cursor.rowcount > 0
        conn.close()
        return ok

    def find_import_rule(self, user_id, text):
        """Find best matching rule for text by keyword inclusion."""
        source = (text or "").lower()
        if not source:
            return None
        rules = self.get_import_rules(user_id)
        for r in rules:
            kw = (r.get("keyword") or "").lower().strip()
            if kw and kw in source:
                return r
        return None

    # Category operations
    def add_category(self, user_id, name, cat_type, color="", icon=""):
        """Add category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO categories (user_id, name, type, color, icon)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, name, cat_type, color, icon))
            conn.commit()
            category_id = cursor.lastrowid
            conn.close()
            return category_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def get_categories(self, user_id, cat_type=None):
        """Get user categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cat_type:
            cursor.execute('''
                SELECT * FROM categories 
                WHERE user_id = ? AND type = ?
                ORDER BY name
            ''', (user_id, cat_type))
        else:
            cursor.execute('SELECT * FROM categories WHERE user_id = ? ORDER BY name', (user_id,))
        
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categories

    # Summary statistics
    def get_summary(self, user_id, start_date=None, end_date=None):
        """Get financial summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE user_id = ?"
        params = [user_id]
        
        if start_date and end_date:
            where_clause += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        cursor.execute(f'SELECT COALESCE(SUM(amount), 0) as total FROM expenses {where_clause}', params)
        total_expenses = cursor.fetchone()[0]
        
        cursor.execute(f'SELECT COALESCE(SUM(amount), 0) as total FROM income {where_clause}', params)
        total_income = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': total_income - total_expenses
        }

    def get_category_summary(self, user_id, start_date=None, end_date=None):
        """Get expenses by category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        where_clause = "WHERE user_id = ?"
        params = [user_id]
        
        if start_date and end_date:
            where_clause += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        cursor.execute(f'''
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM expenses {where_clause}
            GROUP BY category
            ORDER BY total DESC
        ''', params)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # ============== NEW FEATURES FOR 50+ FUNCTIONALITY ==============
    
    # Spending Trends & Analytics
    def get_monthly_spending_trend(self, user_id, months=12):
        """Get monthly spending trend for visualization"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f'''
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(amount) as total,
                COUNT(*) as count,
                AVG(amount) as average
            FROM expenses 
            WHERE user_id = ?
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT ?
        ''', (user_id, months))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_spending_velocity(self, user_id, days=30):
        """Get average daily spending"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(*) as transaction_count,
                SUM(amount) as total,
                AVG(amount) as daily_average
            FROM expenses 
            WHERE user_id = ? AND date >= date('now', '-' || ? || ' days')
        ''', (user_id, days))
        
        result = dict(cursor.fetchone())
        conn.close()
        if result['daily_average']:
            result['daily_average'] = result['daily_average']
        return result

    def get_year_over_year_comparison(self, user_id):
        """Compare current year with last year"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                strftime('%Y', date) as year,
                strftime('%m', date) as month,
                SUM(amount) as total
            FROM expenses 
            WHERE user_id = ?
            GROUP BY year, month
            ORDER BY year DESC, month DESC
        ''', (user_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_top_categories(self, user_id, limit=5):
        """Get top spending categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                category,
                SUM(amount) as total,
                COUNT(*) as count,
                AVG(amount) as average
            FROM expenses 
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_top_vendors(self, user_id, limit=10):
        """Get top vendors/merchants"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                description,
                COUNT(*) as frequency,
                SUM(amount) as total,
                AVG(amount) as average
            FROM expenses 
            WHERE user_id = ? AND description IS NOT NULL
            GROUP BY description
            ORDER BY total DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_largest_transactions(self, user_id, limit=10):
        """Get largest transactions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM expenses 
            WHERE user_id = ?
            ORDER BY amount DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_recurring_transactions(self, user_id):
        """Detect potentially recurring transactions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                category,
                amount,
                COUNT(*) as frequency,
                payment_method
            FROM expenses 
            WHERE user_id = ?
            GROUP BY category, amount, payment_method
            HAVING frequency > 2
            ORDER BY frequency DESC
        ''', (user_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # Budget Analysis
    def get_budget_vs_actual(self, user_id, month, year):
        """Compare budget to actual spending"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, limit_amount FROM budgets 
            WHERE user_id = ? AND month = ? AND year = ?
        ''', (user_id, month, year))
        
        budgets = {row['category']: row['limit_amount'] for row in cursor.fetchall()}
        
        cursor.execute('''
            SELECT 
                category,
                SUM(amount) as actual
            FROM expenses 
            WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
            GROUP BY category
        ''', (user_id, str(month).zfill(2), str(year)))
        
        actuals = {row['category']: row['actual'] for row in cursor.fetchall()}
        conn.close()
        
        # Combine data (compatible with both legacy and new UI keys)
        all_categories = set(budgets.keys()) | set(actuals.keys())
        result = []
        for cat in sorted(all_categories):
            budget = budgets.get(cat, 0)
            actual = actuals.get(cat, 0)
            variance = budget - actual if budget > 0 else actual
            variance_pct = (variance / budget * 100) if budget > 0 else 0
            usage_percent = (actual / budget * 100) if budget > 0 else 0
            result.append({
                'category': cat,
                'budget': budget,
                'actual': actual,
                'variance': variance,
                'variance_pct': variance_pct,
                'status': 'under' if actual <= budget else 'over',
                'limit_amount': budget,
                'spent': actual,
                'remaining': budget - actual,
                'usage_percent': usage_percent,
            })
        return result

    # Savings & Goals
    def get_savings_rate(self, user_id):
        """Calculate savings rate (amount saved / total income)"""
        summary = self.get_summary(user_id)
        if summary['total_income'] > 0:
            rate = (summary['balance'] / summary['total_income']) * 100
        else:
            rate = 0
        return rate

    def get_expense_to_income_ratio(self, user_id):
        """Get expense to income ratio"""
        summary = self.get_summary(user_id)
        if summary['total_income'] > 0:
            ratio = (summary['total_expenses'] / summary['total_income']) * 100
        else:
            ratio = 100 if summary['total_expenses'] > 0 else 0
        return ratio

    # Cash Flow Analysis
    def get_cash_flow_by_date(self, user_id, start_date, end_date):
        """Get daily cash flow (income - expenses)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, SUM(CASE WHEN 'expenses' THEN -amount ELSE amount END) as net_flow
            FROM (
                SELECT date, amount FROM expenses WHERE user_id = ?
                UNION ALL
                SELECT date, amount FROM income WHERE user_id = ?
            )
            WHERE date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (user_id, user_id, start_date, end_date))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_balance_history(self, user_id, months=12):
        """Get running balance over time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(CASE WHEN user_id = ? THEN amount ELSE 0 END) as income_total,
                SUM(CASE WHEN user_id = ? THEN -amount ELSE 0 END) as expense_total
            FROM (
                SELECT date, amount FROM income WHERE user_id = ?
                UNION ALL
                SELECT date, amount FROM expenses WHERE user_id = ?
            )
            GROUP BY month
            ORDER BY month
        ''', (user_id, user_id, user_id, user_id))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # Expense Forecast
    def get_expense_forecast(self, user_id, days_ahead=30):
        """Forecast future expenses based on historical data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                category,
                AVG(amount) as avg_amount,
                COUNT(*) as frequency
            FROM expenses 
            WHERE user_id = ? AND date >= date('now', '-90 days')
            GROUP BY category
        ''', (user_id,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # Transaction Search & Filter
    def search_transactions(self, user_id, query):
        """Search transactions by description, category, or notes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM expenses 
            WHERE user_id = ? AND (
                category LIKE ? OR 
                description LIKE ? OR 
                notes LIKE ?
            )
            ORDER BY date DESC
        ''', (user_id, f'%{query}%', f'%{query}%', f'%{query}%'))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def filter_transactions(self, user_id, category=None, min_amount=None, max_amount=None, start_date=None, end_date=None):
        """Filter transactions by multiple criteria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM expenses WHERE user_id = ?"
        params = [user_id]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        if min_amount is not None:
            query += " AND amount >= ?"
            params.append(min_amount)
        if max_amount is not None:
            query += " AND amount <= ?"
            params.append(max_amount)
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    # Financial Metrics
    def get_financial_health_score(self, user_id):
        """Calculate overall financial health score (0-100)"""
        summary = self.get_summary(user_id)
        savings_rate = self.get_savings_rate(user_id)
        
        score = 0
        # Balance check (max 30 points)
        if summary['balance'] > 10000:
            score += 30
        elif summary['balance'] > 5000:
            score += 20
        elif summary['balance'] > 0:
            score += 10
        
        # Savings rate (max 40 points)
        if savings_rate >= 30:
            score += 40
        elif savings_rate >= 20:
            score += 30
        elif savings_rate >= 10:
            score += 20
        elif savings_rate >= 0:
            score += 10
        
        # Expense ratio (max 30 points)
        expense_ratio = self.get_expense_to_income_ratio(user_id)
        if expense_ratio <= 50:
            score += 30
        elif expense_ratio <= 70:
            score += 20
        elif expense_ratio <= 90:
            score += 10
        
        return min(100, max(0, score))

    # Duplicate Detection
    def find_duplicate_transactions(self, user_id, tolerance=0.05):
        """Find potentially duplicate transactions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM expenses 
            WHERE user_id = ?
            ORDER BY date DESC, amount DESC
        ''', (user_id,))
        
        transactions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        duplicates = []
        for i, trans1 in enumerate(transactions):
            for trans2 in transactions[i+1:]:
                # Check if same category, similar amount, and recent
                base_amount = float(trans1['amount'] or 0)
                if base_amount == 0:
                    continue
                if (trans1['category'] == trans2['category'] and
                    abs(trans1['amount'] - trans2['amount']) / base_amount <= tolerance and
                    (datetime.strptime(trans1['date'], '%Y-%m-%d') - 
                     datetime.strptime(trans2['date'], '%Y-%m-%d')).days <= 7):
                    duplicates.append((trans1, trans2))
        
        return duplicates

    # Additional utility methods
    def get_expense_by_id(self, expense_id):
        """Get specific expense"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_income_by_id(self, income_id):
        """Get specific income"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM income WHERE id = ?', (income_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_statistics_summary(self, user_id):
        """Get comprehensive statistics"""
        return {
            'financial_summary': self.get_summary(user_id),
            'category_summary': self.get_category_summary(user_id),
            'top_categories': self.get_top_categories(user_id, 5),
            'largest_transactions': self.get_largest_transactions(user_id, 5),
            'monthly_trend': self.get_monthly_spending_trend(user_id, 6),
            'savings_rate': self.get_savings_rate(user_id),
            'expense_ratio': self.get_expense_to_income_ratio(user_id),
            'health_score': self.get_financial_health_score(user_id),
            'spending_velocity': self.get_spending_velocity(user_id, 30),
            'recurring_transactions': self.get_recurring_transactions(user_id),
        }

    # ========== MANAGED ACCOUNTS METHODS ==========
    
    def create_account(self, user_id, account_name, account_type="Individual", email="", phone="", note=""):
        """Create a new managed account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO managed_accounts 
                (user_id, account_name, account_type, email, phone, notes, color, icon, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, account_name, account_type, email, phone, note, "#3b82f6", "👤"))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            return None
        finally:
            conn.close()

    def get_managed_accounts(self, user_id):
        """Get all managed accounts for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM managed_accounts 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        accounts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return accounts

    def get_account(self, account_id, user_id):
        """Get specific account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM managed_accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def update_account(self, account_id, user_id, **kwargs):
        """Update account details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        allowed_fields = ['account_name', 'account_type', 'email', 'phone', 'address', 'city', 'notes', 'color', 'icon']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            conn.close()
            return False
        
        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [account_id, user_id]
        
        try:
            cursor.execute(f'''
                UPDATE managed_accounts 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', values)
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def delete_account(self, account_id, user_id):
        """Delete managed account and clean up transactions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Delete account transactions
            cursor.execute('DELETE FROM expenses WHERE account_id = ? AND user_id = ?', (account_id, user_id))
            cursor.execute('DELETE FROM income WHERE account_id = ? AND user_id = ?', (account_id, user_id))
            # Delete account
            cursor.execute('DELETE FROM managed_accounts WHERE id = ? AND user_id = ?', (account_id, user_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def add_expense_to_account(self, user_id, account_id, category, amount, date, description="", payment_method="", notes=""):
        """Add expense to specific account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO expenses 
                (user_id, account_id, category, amount, date, description, payment_method, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, account_id, category, amount, date, description, payment_method, notes))
            conn.commit()
            return cursor.lastrowid
        except:
            return None
        finally:
            conn.close()

    def get_account_expenses(self, user_id, account_id, start_date=None, end_date=None):
        """Get expenses for specific account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if start_date and end_date:
            cursor.execute('''
                SELECT * FROM expenses 
                WHERE user_id = ? AND account_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (user_id, account_id, start_date, end_date))
        else:
            cursor.execute('''
                SELECT * FROM expenses 
                WHERE user_id = ? AND account_id = ?
                ORDER BY date DESC
            ''', (user_id, account_id))
        expenses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return expenses

    def get_account_summary(self, user_id, account_id):
        """Get financial summary for account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total income
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE user_id = ? AND account_id = ?', 
                      (user_id, account_id))
        income = cursor.fetchone()['total']
        
        # Total expenses
        cursor.execute('SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = ? AND account_id = ?',
                      (user_id, account_id))
        expenses = cursor.fetchone()['total']
        
        conn.close()
        return {
            'total_income': income,
            'total_expenses': expenses,
            'balance': income - expenses
        }

    def get_account_category_summary(self, user_id, account_id):
        """Get category breakdown for account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT category, COUNT(*) as count, SUM(amount) as total
            FROM expenses 
            WHERE user_id = ? AND account_id = ?
            GROUP BY category 
            ORDER BY total DESC
        ''', (user_id, account_id))
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return categories

    # ========== GOALS METHODS ==========
    def add_financial_goal(self, user_id, title, target_amount, due_date="", category="General", notes=""):
        """Create a new financial goal."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO financial_goals (user_id, title, target_amount, due_date, category, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, title, target_amount, due_date or None, category, notes)
        )
        conn.commit()
        goal_id = cursor.lastrowid
        conn.close()
        return goal_id

    def get_financial_goals(self, user_id, active_only=False):
        """List goals for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute(
                '''
                SELECT * FROM financial_goals
                WHERE user_id = ? AND status = 'active'
                ORDER BY due_date IS NULL, due_date ASC, id DESC
                ''',
                (user_id,)
            )
        else:
            cursor.execute(
                '''
                SELECT * FROM financial_goals
                WHERE user_id = ?
                ORDER BY due_date IS NULL, due_date ASC, id DESC
                ''',
                (user_id,)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_financial_goal(self, goal_id, user_id, **kwargs):
        """Update financial goal fields."""
        allowed = {"title", "target_amount", "current_amount", "due_date", "category", "notes", "status"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [goal_id, user_id]
        cursor.execute(
            f'''
            UPDATE financial_goals
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_financial_goal(self, goal_id, user_id):
        """Delete goal by id."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM financial_goals WHERE id = ? AND user_id = ?', (goal_id, user_id))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # ========== NOTIFICATIONS METHODS ==========
    def add_notification(self, user_id, title, message, severity="info"):
        """Insert an in-app notification."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO notifications (user_id, title, message, severity, is_read)
            VALUES (?, ?, ?, ?, 0)
            ''',
            (user_id, title, message, severity)
        )
        conn.commit()
        notification_id = cursor.lastrowid
        conn.close()
        return notification_id

    def get_notifications(self, user_id, unread_only=False, limit=150):
        """Fetch notifications for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if unread_only:
            cursor.execute(
                '''
                SELECT * FROM notifications
                WHERE user_id = ? AND is_read = 0
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
        else:
            cursor.execute(
                '''
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (user_id, limit)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def mark_notification_read(self, notification_id, user_id, is_read=True):
        """Mark a notification read/unread."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = ? WHERE id = ? AND user_id = ?',
            (1 if is_read else 0, notification_id, user_id)
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def clear_notifications(self, user_id):
        """Delete all notifications for user."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications WHERE user_id = ?', (user_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted

    def delete_notification(self, notification_id, user_id):
        """Delete one notification."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications WHERE id = ? AND user_id = ?', (notification_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def generate_system_notifications(self, user_id):
        """Generate key alerts from current budget/recurring states."""
        created = 0
        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now()
        try:
            budget_rows = self.get_budget_vs_actual(user_id, now.month, now.year)
        except Exception:
            budget_rows = []
        for row in budget_rows:
            limit_amt = float(row.get("limit_amount", 0) or 0)
            spent = float(row.get("actual_spent", 0) or 0)
            if limit_amt <= 0:
                continue
            ratio = spent / limit_amt
            if ratio >= 1:
                self.add_notification(
                    user_id,
                    "Budget Exceeded",
                    f"{row.get('category', 'Category')} exceeded budget by {(ratio - 1) * 100:.1f}%.",
                    "danger"
                )
                created += 1
            elif ratio >= 0.8:
                self.add_notification(
                    user_id,
                    "Budget Warning",
                    f"{row.get('category', 'Category')} has reached {ratio * 100:.1f}% of budget.",
                    "warning"
                )
                created += 1

        due_bills = [
            b for b in self.get_recurring_bills(user_id, active_only=True)
            if b.get("next_due_date", "") and b.get("next_due_date", "") <= today
        ]
        if due_bills:
            self.add_notification(
                user_id,
                "Recurring Bills Due",
                f"{len(due_bills)} recurring bill(s) are due or overdue.",
                "danger"
            )
            created += 1

        summary = self.get_summary(user_id)
        balance = float(summary.get("balance", 0) or 0)
        if balance < 0:
            self.add_notification(
                user_id,
                "Negative Balance Warning",
                "Your current balance is negative. Review spending and planned bills.",
                "danger"
            )
            created += 1
        return created

    # ========== NOTES METHODS ==========
    def add_quick_note(self, user_id, title, body="", color_tag="blue", is_pinned=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO quick_notes (user_id, title, body, color_tag, is_pinned)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (user_id, title, body, color_tag, int(is_pinned))
        )
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()
        return note_id

    def get_quick_notes(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT * FROM quick_notes
            WHERE user_id = ?
            ORDER BY is_pinned DESC, updated_at DESC
            ''',
            (user_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_quick_note(self, note_id, user_id, **kwargs):
        allowed = {"title", "body", "color_tag", "is_pinned"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [note_id, user_id]
        cursor.execute(
            f'''
            UPDATE quick_notes
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_quick_note(self, note_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quick_notes WHERE id = ? AND user_id = ?', (note_id, user_id))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # ========== REMINDERS METHODS ==========
    def add_reminder(self, user_id, title, due_date, priority="medium", note=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO reminders (user_id, title, due_date, priority, note, is_done)
            VALUES (?, ?, ?, ?, ?, 0)
            ''',
            (user_id, title, due_date, priority, note)
        )
        conn.commit()
        reminder_id = cursor.lastrowid
        conn.close()
        return reminder_id

    def get_reminders(self, user_id, pending_only=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        if pending_only:
            cursor.execute(
                '''
                SELECT * FROM reminders
                WHERE user_id = ? AND is_done = 0
                ORDER BY due_date ASC, updated_at DESC
                ''',
                (user_id,)
            )
        else:
            cursor.execute(
                '''
                SELECT * FROM reminders
                WHERE user_id = ?
                ORDER BY is_done ASC, due_date ASC, updated_at DESC
                ''',
                (user_id,)
            )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_reminder(self, reminder_id, user_id, **kwargs):
        allowed = {"title", "due_date", "priority", "note", "is_done"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        conn = self.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [reminder_id, user_id]
        cursor.execute(
            f'''
            UPDATE reminders
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            ''',
            values
        )
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    def delete_reminder(self, reminder_id, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, user_id))
        conn.commit()
        changed = cursor.rowcount > 0
        conn.close()
        return changed

    # ========== DATA QUALITY ==========
    def get_data_quality_report(self, user_id):
        """Return data-quality gaps and duplicate signals."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) as c FROM expenses WHERE user_id = ? AND (description IS NULL OR TRIM(description) = '')",
            (user_id,)
        )
        missing_exp_desc = int(cursor.fetchone()["c"])

        cursor.execute(
            "SELECT COUNT(*) as c FROM income WHERE user_id = ? AND (description IS NULL OR TRIM(description) = '')",
            (user_id,)
        )
        missing_inc_desc = int(cursor.fetchone()["c"])

        cursor.execute(
            "SELECT COUNT(*) as c FROM expenses WHERE user_id = ? AND (category IS NULL OR TRIM(category) = '' OR category = 'Other')",
            (user_id,)
        )
        uncategorized_exp = int(cursor.fetchone()["c"])
        conn.close()

        duplicates = self.find_duplicate_transactions(user_id, tolerance=0.01)
        return {
            "missing_expense_descriptions": missing_exp_desc,
            "missing_income_descriptions": missing_inc_desc,
            "uncategorized_expenses": uncategorized_exp,
            "possible_duplicates": len(duplicates),
        }

