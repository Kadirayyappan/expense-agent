"""
Step 3: Store categorized transactions in a SQLite database.

SQLite needs no server/installation - it's just a file (expenses.db).
This is where your SQL knowledge becomes directly useful.
"""

import sqlite3

DB_NAME = "expenses.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            merchant TEXT,
            amount REAL,
            category TEXT
        )
    """)
    conn.commit()
    conn.close()


def insert_transaction(date, merchant, amount, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (date, merchant, amount, category) VALUES (?, ?, ?, ?)",
        (date, merchant, amount, category),
    )
    conn.commit()
    conn.close()


def insert_transactions_bulk(rows):
    """
    Insert many transactions in ONE database connection instead of one per row.
    'rows' is a list of tuples: (date, merchant, amount, category)
    Much faster for large files (500+ rows) than calling insert_transaction in a loop.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO transactions (date, merchant, amount, category) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def get_all_transactions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, merchant, amount, category FROM transactions")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_spending_by_category():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        GROUP BY category
        ORDER BY total DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def clear_table():
    """Useful when re-uploading a file during testing."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()