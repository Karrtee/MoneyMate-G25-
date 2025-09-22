from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# -------------------------
# Database Setup
# -------------------------
DB_NAME = "moneymate.db"

def init_db():
    """Create database and transactions table if not exists"""
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income','expense'))
            )
        """)
        conn.commit()
        conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB when app starts
init_db()

# -------------------------
# Routes
# -------------------------

@app.route('/')
def home():
    """Show login page as the main page"""
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        # Here you would save the user to the database
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Here you would check user credentials
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard with summary and charts"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Totals
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income'")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense'")
    total_expense = cursor.fetchone()[0] or 0

    balance = total_income - total_expense

    # All transactions
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    transactions = cursor.fetchall()

    # Pie chart: Expenses by category
    cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' GROUP BY category")
    category_data = cursor.fetchall()
    pie_labels = [row['category'] for row in category_data]
    pie_values = [row['SUM(amount)'] for row in category_data]

    # Bar chart: Monthly expenses
    cursor.execute("SELECT strftime('%Y-%m', date) AS month, SUM(amount) FROM transactions WHERE type='expense' GROUP BY month")
    monthly_data = cursor.fetchall()
    bar_labels = [row['month'] for row in monthly_data]
    bar_values = [row['SUM(amount)'] for row in monthly_data]

    conn.close()

    return render_template("dashboard.html",
                           income=total_income,
                           expense=total_expense,
                           balance=balance,
                           transactions=transactions,
                           pie_labels=pie_labels,
                           pie_values=pie_values,
                           bar_labels=bar_labels,
                           bar_values=bar_values)

@app.route('/add', methods=['GET', 'POST'])
def add_transaction():
    """Add a new transaction"""
    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']
        date = request.form['date']
        t_type = request.form['type']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (amount, category, description, date, type)
            VALUES (?, ?, ?, ?, ?)
        """, (amount, category, description, date, t_type))
        conn.commit()
        conn.close()

        flash('Transaction added!', 'success')
        return redirect(url_for('dashboard'))

    return render_template("add.html")

@app.route('/transactions')
def list_transactions():
    """Show all transactions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions ORDER BY date DESC")
    transactions = cursor.fetchall()
    conn.close()
    return render_template("transactions.html", transactions=transactions)

@app.route('/transaction/<int:transaction_id>')
def view_transaction(transaction_id):
    """View a single transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    transaction = cursor.fetchone()
    conn.close()

    if transaction is None:
        flash("Transaction not found.", "danger")
        return redirect(url_for('list_transactions'))

    return render_template("transaction_detail.html", transaction=transaction)

@app.route('/delete/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    """Delete a transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
    flash('Transaction deleted.', 'info')
    return redirect(url_for('list_transactions'))

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)