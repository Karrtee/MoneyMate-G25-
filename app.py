from flask import Flask, render_template
import sqlite3
import os

# Initialize Flask app
app = Flask(__name__)

# -------------------------
# Database Setup (Week 1: Just create the file and table if missing)
# -------------------------
DB_NAME = "moneymate.db"

def init_db():
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

# Call DB init at startup
init_db()

# -------------------------
# Routes
# -------------------------

# Home route (Karrtee will design later)
@app.route('/')
def home():
    return render_template("index.html")

# Dashboard route (Farhan's part)
@app.route('/dashboard')
def dashboard():
    # Week 1: Dummy values
    total_income = 0
    total_expense = 0
    balance = total_income - total_expense
    return render_template("dashboard.html",
                           income=total_income,
                           expense=total_expense,
                           balance=balance)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
