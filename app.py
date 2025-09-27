from flask import session
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
    """Create database and tables if not exists"""
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
                type TEXT NOT NULL CHECK(type IN ('income','expense')),
                user_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
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
    print("Home route accessed")
    """Show login page as the main page"""
    return redirect(url_for('login'))

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
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
            return render_template('register.html')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']  # Store user ID in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Main dashboard with summary and charts"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Totals
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND user_id=?", (user_id,))
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND user_id=?", (user_id,))
    total_expense = cursor.fetchone()[0] or 0

    balance = total_income - total_expense

    # All transactions
    cursor.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,))
    transactions = cursor.fetchall()

    # Pie chart: Expenses by category
    cursor.execute("SELECT category, SUM(amount) FROM transactions WHERE type='expense' AND user_id=? GROUP BY category", (user_id,))
    category_data = cursor.fetchall()
    pie_labels = [row['category'] for row in category_data]
    pie_values = [row['SUM(amount)'] for row in category_data]

    # Bar chart: Monthly expenses
    cursor.execute("SELECT strftime('%Y-%m', date) AS month, SUM(amount) FROM transactions WHERE type='expense' AND user_id=? GROUP BY month", (user_id,))
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
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']
        date = request.form['date']
        t_type = request.form['type']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transactions (amount, category, description, date, type, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (amount, category, description, date, t_type, user_id))
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

@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
    transaction = cursor.fetchone()

    if not transaction:
        conn.close()
        flash('Transaction not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form['category']
        description = request.form['description']
        date = request.form['date']
        t_type = request.form['type']

        cursor.execute("""
            UPDATE transactions
            SET amount = ?, category = ?, description = ?, date = ?, type = ?
            WHERE id = ?
        """, (amount, category, description, date, t_type, transaction_id))
        
        conn.commit()
        conn.close()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    conn.close()
    return render_template('edit.html', transaction=transaction)


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True)