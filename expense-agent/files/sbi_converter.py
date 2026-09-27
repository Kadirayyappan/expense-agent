"""
Converts an SBI bank statement (CSV/Excel export) into the format
our expense agent app understands: date, merchant, amount

HOW TO USE:
1. Export your SBI statement as CSV or Excel from net banking / YONO
2. Save it in this same folder, e.g. "sbi_statement.csv"
3. Run: python sbi_converter.py sbi_statement.csv
4. It creates "converted_transactions.csv" - upload THIS into the app

NOTE: This only keeps DEBIT transactions (money going out = spending).
Credits (money coming in, like salary) are excluded since this app
tracks expenses, not income. You can change this if you want both.
"""

import pandas as pd
import sys
import re


def find_column(columns, keywords):
    """Find a column name that contains any of the given keywords (case-insensitive)."""
    for col in columns:
        col_lower = str(col).lower().strip()
        for kw in keywords:
            if kw in col_lower:
                return col
    return None


def clean_amount(value):
    """SBI amounts sometimes come as strings like '1,200.00' or with extra spaces."""
    if pd.isna(value):
        return 0.0
    value_str = str(value).replace(",", "").strip()
    if value_str in ("", "-", "nan"):
        return 0.0
    try:
        return float(value_str)
    except ValueError:
        return 0.0


def convert_sbi_statement(input_path: str, output_path: str = "converted_transactions.csv"):
    # Try reading as CSV first, fall back to Excel
    if input_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(input_path)
    else:
        # SBI CSV exports sometimes have a few header/disclaimer rows before the real table.
        # Try a few skiprows values until we find one that has recognizable columns.
        df = None
        for skip in range(0, 25):
            try:
                temp = pd.read_csv(input_path, skiprows=skip, encoding="utf-8", on_bad_lines="skip")
            except Exception:
                try:
                    temp = pd.read_csv(input_path, skiprows=skip, encoding="latin1", on_bad_lines="skip")
                except Exception:
                    continue
            cols_lower = [str(c).lower() for c in temp.columns]
            if any("date" in c for c in cols_lower) and any(
                ("debit" in c or "withdrawal" in c or "amount" in c) for c in cols_lower
            ):
                df = temp
                break
        if df is None:
            raise ValueError(
                "Could not automatically detect the statement table. "
                "Open the CSV in a text editor and check how many rows come before the real header row, "
                "then tell me that number and I'll adjust the script."
            )

    df.columns = [str(c).strip() for c in df.columns]

    date_col = find_column(df.columns, ["txn date", "transaction date", "date", "value date"])
    desc_col = find_column(df.columns, ["description", "narration", "particulars", "remarks"])
    debit_col = find_column(df.columns, ["debit", "withdrawal"])
    credit_col = find_column(df.columns, ["credit", "deposit"])

    if not date_col or not desc_col or not debit_col:
        raise ValueError(
            f"Couldn't find expected columns. Found these instead: {list(df.columns)}\n"
            f"Detected -> date: {date_col}, description: {desc_col}, debit: {debit_col}\n"
            "Paste this column list back to me and I'll fix the script."
        )

    df["_amount"] = df[debit_col].apply(clean_amount)
    df = df[df["_amount"] > 0]  # keep only actual debit (spending) rows

    result = pd.DataFrame({
        "date": pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.strftime("%Y-%m-%d"),
        "merchant": df[desc_col].astype(str).str.strip(),
        "amount": df["_amount"],
    })

    result = result.dropna(subset=["date"])
    result = result[result["merchant"] != ""]

    result.to_csv(output_path, index=False)
    print(f"Converted {len(result)} spending transactions.")
    print(f"Saved to: {output_path}")
    print("\nPreview:")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sbi_converter.py your_statement.csv")
        sys.exit(1)
    convert_sbi_statement(sys.argv[1])
