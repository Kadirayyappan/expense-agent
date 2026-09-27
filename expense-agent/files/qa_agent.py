"""
PHASE 2 - Step B: A real text-to-SQL agent, powered by Gemini.

This is what makes the project a genuine "agent" rather than just an
automation script. The flow is:

  1. You ask a question in plain English
  2. Gemini looks at your database structure (schema) and WRITES a SQL query
  3. We run that query safely
  4. Gemini turns the raw result back into a plain English answer

This "write code -> run it -> explain the result" loop is the essence of
how agents work.
"""

import os
import sqlite3
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

MODEL_NAME = "gemini-3.5-flash-lite"
DB_NAME = "expenses.db"

# We tell the LLM exactly what the table looks like so it can write correct SQL.
SCHEMA_DESCRIPTION = """
Table name: transactions
Columns:
  - id (integer)
  - date (text, format YYYY-MM-DD)
  - merchant (text)
  - amount (real number, in rupees)
  - category (text, one of: Food, Transport, Bills, Shopping, Entertainment, Other)
"""


def generate_sql(question: str) -> str:
    """Ask Gemini to convert a plain-English question into a SQL query."""
    prompt = f"""You are a SQL expert. Given this database schema:
{SCHEMA_DESCRIPTION}

Write a SINGLE SQLite SQL query that answers this question:
"{question}"

Rules:
- Only write SELECT queries. Never write INSERT, UPDATE, DELETE, or DROP.
- Reply with ONLY the raw SQL query, no explanation, no markdown formatting.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0),  # 0 = consistent, not creative
    )

    sql = response.text.strip()
    # Clean up in case the model wraps it in ```sql ... ``` anyway
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql


def is_safe_query(sql: str) -> bool:
    """
    SAFETY CHECK - very important for any agent that can run its own code.
    We only ever allow SELECT queries, nothing that modifies the database.
    """
    sql_lower = sql.lower().strip()
    forbidden = ["insert", "update", "delete", "drop", "alter", "create"]
    if not sql_lower.startswith("select"):
        return False
    if any(word in sql_lower for word in forbidden):
        return False
    return True


def run_query(sql: str):
    """Execute the SQL query and return results."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, rows


def explain_result(question: str, columns: list, rows: list) -> str:
    """Ask Gemini to turn raw SQL results into a natural-language answer."""
    prompt = f"""The user asked: "{question}"

The SQL query returned this data:
Columns: {columns}
Rows: {rows}

Write a short, friendly, one or two sentence answer in plain English based on this data.
If the data is empty, say so clearly."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return response.text.strip()


def ask_agent(question: str) -> dict:
    """
    The main agent function - this is what app.py calls.
    Returns a dict with the SQL used, the raw data, and the final answer,
    so you can show your "agent trace" in the UI (great for demos/interviews).
    """
    sql = generate_sql(question)

    if not is_safe_query(sql):
        return {
            "sql": sql,
            "error": "Blocked an unsafe query for security reasons.",
            "answer": "I can only answer questions that read data, not modify it.",
        }

    try:
        columns, rows = run_query(sql)
        answer = explain_result(question, columns, rows)
        return {"sql": sql, "columns": columns, "rows": rows, "answer": answer}
    except Exception as e:
        return {"sql": sql, "error": str(e), "answer": "I couldn't run that query. Try rephrasing your question."}


if __name__ == "__main__":
    # Quick test - make sure you've run app.py at least once so expenses.db exists
    result = ask_agent("What did I spend the most on?")
    print("SQL used:", result["sql"])
    print("Answer:", result["answer"])
