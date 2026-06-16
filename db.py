"""SQLite storage. Stdlib only — 6 clients, no need for an ORM."""
import json
import os
import sqlite3

DB_PATH = os.environ.get("RAILWAY_DATABASE_PATH", os.path.join(os.path.dirname(__file__), "portal.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_married INTEGER NOT NULL DEFAULT 0,
            name1 TEXT NOT NULL,
            dob1 TEXT,
            ssn1_last4 TEXT,
            name2 TEXT,
            dob2 TEXT,
            ssn2_last4 TEXT,
            monthly_salary REAL DEFAULT 0,          -- Inflow
            monthly_expense_budget REAL DEFAULT 0,  -- Outflow
            insurance_deductibles_total REAL DEFAULT 0,
            private_reserve_balance REAL DEFAULT 0,
            schwab_balance REAL DEFAULT 0,
            accounts_json TEXT DEFAULT '[]',        -- list of account dicts
            last_report_date TEXT
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            quarter_label TEXT,
            snapshot_json TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        );
        """
    )
    conn.commit()
    conn.close()


# ---- client helpers -------------------------------------------------------
def list_clients():
    conn = get_db()
    rows = conn.execute("SELECT * FROM clients ORDER BY name1").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(client_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    conn.close()
    if not row:
        return None
    c = dict(row)
    c["accounts"] = json.loads(c.get("accounts_json") or "[]")
    return c


def save_client(data, client_id=None):
    conn = get_db()
    fields = (
        data.get("is_married", 0),
        data.get("name1", ""),
        data.get("dob1"),
        data.get("ssn1_last4"),
        data.get("name2"),
        data.get("dob2"),
        data.get("ssn2_last4"),
        data.get("monthly_salary", 0),
        data.get("monthly_expense_budget", 0),
        data.get("insurance_deductibles_total", 0),
        data.get("private_reserve_balance", 0),
        data.get("schwab_balance", 0),
        json.dumps(data.get("accounts", [])),
    )
    if client_id:
        conn.execute(
            """UPDATE clients SET is_married=?, name1=?, dob1=?, ssn1_last4=?, name2=?,
               dob2=?, ssn2_last4=?, monthly_salary=?, monthly_expense_budget=?,
               insurance_deductibles_total=?, private_reserve_balance=?, schwab_balance=?,
               accounts_json=? WHERE id=?""",
            fields + (client_id,),
        )
    else:
        cur = conn.execute(
            """INSERT INTO clients (is_married, name1, dob1, ssn1_last4, name2, dob2,
               ssn2_last4, monthly_salary, monthly_expense_budget, insurance_deductibles_total,
               private_reserve_balance, schwab_balance, accounts_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            fields,
        )
        client_id = cur.lastrowid
    conn.commit()
    conn.close()
    return client_id


def save_report(client_id, quarter_label, snapshot):
    from datetime import datetime
    conn = get_db()
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO reports (client_id, created_at, quarter_label, snapshot_json) VALUES (?,?,?,?)",
        (client_id, now, quarter_label, json.dumps(snapshot)),
    )
    conn.execute("UPDATE clients SET last_report_date=? WHERE id=?", (now, client_id))
    conn.commit()
    conn.close()
