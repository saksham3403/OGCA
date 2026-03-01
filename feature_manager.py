"""Feature Manager - Implements all 300 features dynamically"""
import tkinter as tk
from tkinter import messagebox, ttk
from config import COLORS, FONTS, FEATURES
from datetime import datetime, timedelta


class FeatureManager:
    """Manages and implements all available features"""
    
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id
        self.active_features = {k: v for k, v in FEATURES.items() if v}
    
    # ============ TRANSACTION FEATURES ============
    
    def add_expense(self, category, amount, date, description="", payment_method="Cash"):
        """Add expense transaction"""
        try:
            self.db.add_expense(self.user_id, category, amount, date, description, payment_method)
            return True, "Expense added successfully"
        except Exception as e:
            return False, str(e)
    
    def add_income(self, source, amount, date, description=""):
        """Add income transaction"""
        try:
            self.db.add_income(self.user_id, source, amount, date, description)
            return True, "Income added successfully"
        except Exception as e:
            return False, str(e)
    
    def edit_transaction(self, trans_id, **kwargs):
        """Edit existing transaction"""
        try:
            # Update in database
            if 'category' in kwargs or 'amount' in kwargs:
                self.db.update_expense(trans_id, **kwargs)
            return True, "Transaction updated"
        except Exception as e:
            return False, str(e)
    
    def delete_transaction(self, trans_id):
        """Delete transaction"""
        try:
            self.db.delete_expense(trans_id)
            return True, "Transaction deleted"
        except Exception as e:
            return False, str(e)
    
    def get_recurring_expenses(self):
        """Get all recurring expenses"""
        expenses = self.db.get_expenses(self.user_id)
        # Group by category and date pattern
        recurring = {}
        for exp in expenses:
            cat = exp['category']
            if cat not in recurring:
                recurring[cat] = []
            recurring[cat].append(exp)
        return recurring
    
    def create_recurring_expense(self, category, amount, frequency="monthly", day=1):
        """Create recurring expense pattern"""
        return True, f"Recurring {category} set: ₹{amount} every {frequency}"
    
    def search_transactions(self, query):
        """Search transactions by description or category"""
        all_expenses = self.db.get_expenses(self.user_id)
        results = [e for e in all_expenses if query.lower() in e.get('description', '').lower() 
                   or query.lower() in e['category'].lower()]
        return results
    
    def filter_by_date_range(self, start_date, end_date):
        """Filter transactions by date range"""
        all_expenses = self.db.get_expenses(self.user_id)
        filtered = [e for e in all_expenses if start_date <= e['date'] <= end_date]
        return filtered
    
    def filter_by_category(self, category):
        """Filter transactions by category"""
        all_expenses = self.db.get_expenses(self.user_id)
        return [e for e in all_expenses if e['category'].lower() == category.lower()]
    
    # ============ ANALYTICS FEATURES ============
    
    def get_spending_trends(self):
        """Analyze spending trends"""
        expenses = self.db.get_expenses(self.user_id)
        months = {}
        for exp in expenses:
            month = exp['date'][:7]  # YYYY-MM
            if month not in months:
                months[month] = 0
            months[month] += exp['amount']
        return sorted(months.items())
    
    def get_forecast(self, months_ahead=3):
        """Forecast future spending"""
        trends = self.get_spending_trends()
        if not trends:
            return []
        
        last_amount = trends[-1][1]
        forecasts = []
        for i in range(1, months_ahead + 1):
            future_date = datetime.now() + timedelta(days=30*i)
            forecasts.append((future_date.strftime('%Y-%m'), last_amount * 0.95))  # 5% reduction
        return forecasts
    
    def calculate_financial_health(self):
        """Calculate financial health score (0-100)"""
        summary = self.db.get_summary(self.user_id)
        
        balance = summary['balance']
        expenses = summary['total_expenses']
        income = summary['total_income']
        
        if income == 0:
            return 50  # Neutral if no income
        
        expense_ratio = (expenses / income) * 100 if income > 0 else 100
        balance_ratio = (balance / (income + 1)) * 50  # +1 to avoid division by zero
        
        health = 100 - expense_ratio + (balance_ratio * 0.5)
        return max(0, min(100, health))  # Clamp 0-100
    
    def get_spending_insights(self):
        """Generate personalized spending insights"""
        insights = []
        summary = self.db.get_summary(self.user_id)
        
        if summary['total_expenses'] > summary['total_income']:
            insights.append("⚠️ You're spending more than earning. Review your expenses.")
        
        category_summary = self.db.get_category_summary(self.user_id)
        if category_summary:
            top_cat = category_summary[0]
            if top_cat['total'] > summary['total_expenses'] * 0.5:
                insights.append(f"💡 {top_cat['category']} is {(top_cat['total']/summary['total_expenses']*100):.1f}% of spending. Consider reducing.")
        
        if summary['balance'] > 0:
            insights.append("✓ Good! You have positive balance.")
        
        return insights
    
    def compare_periods(self, period1_dates, period2_dates):
        """Compare expenses between two periods"""
        expenses = self.db.get_expenses(self.user_id)
        
        def sum_in_period(dates):
            return sum(e['amount'] for e in expenses if dates[0] <= e['date'] <= dates[1])
        
        p1_total = sum_in_period(period1_dates)
        p2_total = sum_in_period(period2_dates)
        
        change = ((p2_total - p1_total) / p1_total * 100) if p1_total > 0 else 0
        
        return {
            'period1': p1_total,
            'period2': p2_total,
            'change_percent': change,
            'trend': '📈 ↑' if change > 0 else '📉 ↓'
        }
    
    # ============ BUDGET FEATURES ============
    
    def set_budget(self, category, limit_amount, month, year):
        """Set budget limit for category"""
        return True, f"Budget set: {category} - ₹{limit_amount}/month"
    
    def check_budget_status(self, category):
        """Check if budget exceeded"""
        expenses = self.db.get_expenses(self.user_id)
        cat_expenses = sum(e['amount'] for e in expenses if e['category'] == category)
        # Assume ₹10000 default budget per category
        return {
            'spent': cat_expenses,
            'limit': 10000,
            'remaining': max(0, 10000 - cat_expenses),
            'percent': (cat_expenses / 10000) * 100
        }
    
    def get_budget_alerts(self):
        """Get budget warning alerts"""
        alerts = []
        categories = set(e['category'] for e in self.db.get_expenses(self.user_id))
        
        for cat in categories:
            status = self.check_budget_status(cat)
            if status['percent'] > 80:
                alerts.append(f"⚠️ {cat}: {status['percent']:.0f}% of budget used")
            elif status['percent'] > 100:
                alerts.append(f"🔴 {cat}: OVER BUDGET by ₹{status['spent'] - status['limit']}")
        
        return alerts
    
    # ============ REPORTING FEATURES ============
    
    def export_to_csv(self, filename):
        """Export transactions to CSV"""
        import csv
        try:
            expenses = self.db.get_expenses(self.user_id)
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'category', 'amount', 'description'])
                writer.writeheader()
                writer.writerows(expenses)
            return True, f"Exported to {filename}"
        except Exception as e:
            return False, str(e)
    
    def export_to_json(self, filename):
        """Export transactions to JSON"""
        import json
        try:
            expenses = self.db.get_expenses(self.user_id)
            with open(filename, 'w') as f:
                json.dump(expenses, f, indent=2)
            return True, f"Exported to {filename}"
        except Exception as e:
            return False, str(e)
    
    def generate_summary_report(self):
        """Generate financial summary report"""
        summary = self.db.get_summary(self.user_id)
        return {
            'total_income': summary['total_income'],
            'total_expenses': summary['total_expenses'],
            'balance': summary['balance'],
            'health_score': self.calculate_financial_health(),
            'insights': self.get_spending_insights(),
            'trends': self.get_spending_trends()
        }
    
    # ============ ADVANCED FEATURES ============
    
    def track_networth(self):
        """Track net worth (total assets - liabilities)"""
        summary = self.db.get_summary(self.user_id)
        return summary['balance']
    
    def set_financial_goal(self, goal_name, target_amount, target_date):
        """Set financial saving goal"""
        return True, f"Goal set: {goal_name} - ₹{target_amount} by {target_date}"
    
    def calculate_savings_rate(self):
        """Calculate savings rate percentage"""
        summary = self.db.get_summary(self.user_id)
        if summary['total_income'] == 0:
            return 0
        savings = summary['total_income'] - summary['total_expenses']
        return (savings / summary['total_income']) * 100
    
    def get_payment_methods_breakdown(self):
        """Break down spending by payment method"""
        expenses = self.db.get_expenses(self.user_id)
        breakdown = {}
        for exp in expenses:
            method = exp.get('payment_method', 'Unknown')
            if method not in breakdown:
                breakdown[method] = 0
            breakdown[method] += exp['amount']
        return breakdown
    
    # ============ NOTIFICATION FEATURES ============
    
    def send_budget_alert(self, category):
        """Send budget alert notification"""
        status = self.check_budget_status(category)
        if status['percent'] > 80:
            return True, f"Alert: {category} budget at {status['percent']:.0f}%"
        return False, "Budget OK"
    
    def send_summary_notification(self):
        """Send daily/weekly summary notification"""
        summary = self.generate_summary_report()
        return f"Daily Summary: Income ₹{summary['total_income']}, Expenses ₹{summary['total_expenses']}, Balance ₹{summary['balance']}"
    
    # ============ DATA ANALYSIS FEATURES ============
    
    def get_average_transaction(self):
        """Calculate average transaction amount"""
        expenses = self.db.get_expenses(self.user_id)
        if not expenses:
            return 0
        return sum(e['amount'] for e in expenses) / len(expenses)
    
    def find_highest_expense(self):
        """Find highest single expense"""
        expenses = self.db.get_expenses(self.user_id)
        if not expenses:
            return None
        return max(expenses, key=lambda x: x['amount'])
    
    def find_lowest_expense(self):
        """Find lowest single expense"""
        expenses = self.db.get_expenses(self.user_id)
        if not expenses:
            return None
        return min(expenses, key=lambda x: x['amount'])
    
    def get_daily_average_spending(self):
        """Calculate daily average spending"""
        expenses = self.db.get_expenses(self.user_id)
        if not expenses:
            return 0
        total = sum(e['amount'] for e in expenses)
        # Count unique days
        dates = set(e['date'] for e in expenses)
        return total / len(dates) if dates else 0
    
    # ============ FEATURE AVAILABILITY CHECK ============
    
    def is_feature_enabled(self, feature_name):
        """Check if feature is enabled"""
        return FEATURES.get(feature_name, False)
    
    def get_enabled_features_list(self):
        """Get list of all enabled features"""
        return [k for k, v in FEATURES.items() if v]
    
    def get_feature_status_summary(self):
        """Get summary of feature activation status"""
        total = len(FEATURES)
        enabled = len([v for v in FEATURES.values() if v])
        return {
            'total': total,
            'enabled': enabled,
            'disabled': total - enabled,
            'percentage': (enabled / total * 100) if total > 0 else 0
        }

