"""
Populate the local DB with 4 realistic high-net-worth clients + Q1/Q2 2026 reports.
Run INSIDE Docker: docker compose exec web python seed_demo.py
"""
import db
from calculations import compute_sacs, compute_tcc

db.init_db()

# ── helpers ────────────────────────────────────────────────────────────────────
def snapshot(client):
    sacs = compute_sacs(
        inflow=client["monthly_salary"],
        outflow=client["monthly_expense_budget"],
        insurance_deductibles_total=client["insurance_deductibles_total"],
    )
    tcc = compute_tcc(client["accounts"])
    return {"client": client, "sacs": sacs, "tcc": tcc, "report_date": "2026-06-17"}


def seed(profile, quarters):
    cid = db.save_client(profile)
    client = db.get_client(cid)
    for q, overrides in quarters:
        # Apply quarterly overrides (balance changes between quarters)
        for acct_label, new_bal in overrides.items():
            for a in client["accounts"]:
                if a["label"] == acct_label:
                    a["balance"] = new_bal
        db.save_report(cid, q, snapshot(client))
    print(f"  ✓ {profile['name1']} (id={cid})")
    return cid


# ── Client 1 — Margaret & Thomas Ellison (retired couple, Atlanta) ────────────
seed(
    {
        "is_married": 1,
        "name1": "Margaret Ellison", "dob1": "1958-03-22", "ssn1_last4": "6614",
        "name2": "Thomas Ellison",   "dob2": "1955-11-07", "ssn2_last4": "3872",
        "monthly_salary": 18500,
        "monthly_expense_budget": 13200,
        "insurance_deductibles_total": 8000,
        "private_reserve_balance": 95000,
        "schwab_balance": 620000,
        "accounts": [
            {"label": "Traditional IRA",        "category": "retirement",     "owner": "client1", "last4": "2201", "balance": 580000, "interest_rate": 0,    "address": ""},
            {"label": "Roth IRA",               "category": "retirement",     "owner": "client1", "last4": "4490", "balance": 140000, "interest_rate": 0,    "address": ""},
            {"label": "401(k) — Thomas",        "category": "retirement",     "owner": "client2", "last4": "8831", "balance": 920000, "interest_rate": 0,    "address": ""},
            {"label": "Roth IRA — Thomas",      "category": "retirement",     "owner": "client2", "last4": "5503", "balance": 210000, "interest_rate": 0,    "address": ""},
            {"label": "Joint Brokerage",        "category": "non_retirement", "owner": "joint",   "last4": "7712", "balance": 620000, "interest_rate": 0,    "address": ""},
            {"label": "Primary Residence",      "category": "trust",          "owner": "joint",   "last4": "",     "balance": 1250000,"interest_rate": 0,    "address": "52 Magnolia Way, Buckhead, GA"},
            {"label": "Mortgage",               "category": "liability",      "owner": "joint",   "last4": "",     "balance": 195000, "interest_rate": 4.75, "address": ""},
        ],
    },
    quarters=[
        ("Q1 2026", {
            "Joint Brokerage": 598000, "Traditional IRA": 571000, "401(k) — Thomas": 905000,
        }),
        ("Q2 2026", {
            "Joint Brokerage": 620000, "Traditional IRA": 580000, "401(k) — Thomas": 920000,
        }),
    ],
)

# ── Client 2 — Diana Voss (single, executive, Alpharetta) ─────────────────────
seed(
    {
        "is_married": 0,
        "name1": "Diana Voss", "dob1": "1979-07-30", "ssn1_last4": "5529",
        "name2": "", "dob2": None, "ssn2_last4": "",
        "monthly_salary": 22000,
        "monthly_expense_budget": 14500,
        "insurance_deductibles_total": 5000,
        "private_reserve_balance": 130000,
        "schwab_balance": 415000,
        "accounts": [
            {"label": "Roth IRA",               "category": "retirement",     "owner": "client1", "last4": "9901", "balance": 185000, "interest_rate": 0,    "address": ""},
            {"label": "401(k)",                 "category": "retirement",     "owner": "client1", "last4": "3340", "balance": 395000, "interest_rate": 0,    "address": ""},
            {"label": "Schwab Brokerage",       "category": "non_retirement", "owner": "client1", "last4": "6620", "balance": 415000, "interest_rate": 0,    "address": ""},
            {"label": "Stock Options (vested)", "category": "non_retirement", "owner": "client1", "last4": "",     "balance": 98000,  "interest_rate": 0,    "address": ""},
            {"label": "Primary Residence",      "category": "trust",          "owner": "client1", "last4": "",     "balance": 780000, "interest_rate": 0,    "address": "8 Ridgewood Ct, Alpharetta, GA"},
            {"label": "Mortgage",               "category": "liability",      "owner": "client1", "last4": "",     "balance": 310000, "interest_rate": 5.5,  "address": ""},
            {"label": "Auto Loan",              "category": "liability",      "owner": "client1", "last4": "",     "balance": 38000,  "interest_rate": 6.25, "address": ""},
        ],
    },
    quarters=[
        ("Q1 2026", {
            "Schwab Brokerage": 400000, "401(k)": 380000, "Stock Options (vested)": 87000,
        }),
        ("Q2 2026", {
            "Schwab Brokerage": 415000, "401(k)": 395000, "Stock Options (vested)": 98000,
        }),
    ],
)

# ── Client 3 — Robert & Karen Nakamura (business owner couple, Sandy Springs) ─
seed(
    {
        "is_married": 1,
        "name1": "Robert Nakamura", "dob1": "1965-01-18", "ssn1_last4": "4417",
        "name2": "Karen Nakamura",  "dob2": "1968-09-25", "ssn2_last4": "8803",
        "monthly_salary": 31000,
        "monthly_expense_budget": 19500,
        "insurance_deductibles_total": 12000,
        "private_reserve_balance": 210000,
        "schwab_balance": 895000,
        "accounts": [
            {"label": "SEP-IRA — Robert",       "category": "retirement",     "owner": "client1", "last4": "1147", "balance": 1100000,"interest_rate": 0,    "address": ""},
            {"label": "Roth IRA — Robert",      "category": "retirement",     "owner": "client1", "last4": "7722", "balance": 230000, "interest_rate": 0,    "address": ""},
            {"label": "Traditional IRA — Karen","category": "retirement",     "owner": "client2", "last4": "5581", "balance": 340000, "interest_rate": 0,    "address": ""},
            {"label": "Roth IRA — Karen",       "category": "retirement",     "owner": "client2", "last4": "9934", "balance": 95000,  "interest_rate": 0,    "address": ""},
            {"label": "Joint Brokerage",        "category": "non_retirement", "owner": "joint",   "last4": "3308", "balance": 895000, "interest_rate": 0,    "address": ""},
            {"label": "Checking (Pinnacle)",    "category": "non_retirement", "owner": "joint",   "last4": "2210", "balance": 85000,  "interest_rate": 0,    "address": ""},
            {"label": "Primary Residence",      "category": "trust",          "owner": "joint",   "last4": "",     "balance": 1650000,"interest_rate": 0,    "address": "204 Riverside Dr, Sandy Springs, GA"},
            {"label": "Mortgage",               "category": "liability",      "owner": "joint",   "last4": "",     "balance": 425000, "interest_rate": 4.25, "address": ""},
            {"label": "Business Line of Credit","category": "liability",      "owner": "client1", "last4": "",     "balance": 150000, "interest_rate": 7.5,  "address": ""},
        ],
    },
    quarters=[
        ("Q1 2026", {
            "Joint Brokerage": 870000, "SEP-IRA — Robert": 1075000, "Checking (Pinnacle)": 92000,
        }),
        ("Q2 2026", {
            "Joint Brokerage": 895000, "SEP-IRA — Robert": 1100000, "Checking (Pinnacle)": 85000,
        }),
    ],
)

# ── Client 4 — Patricia Simmons (single, near retirement, Marietta) ───────────
seed(
    {
        "is_married": 0,
        "name1": "Patricia Simmons", "dob1": "1961-06-04", "ssn1_last4": "7781",
        "name2": "", "dob2": None, "ssn2_last4": "",
        "monthly_salary": 12500,
        "monthly_expense_budget": 8800,
        "insurance_deductibles_total": 4500,
        "private_reserve_balance": 68000,
        "schwab_balance": 290000,
        "accounts": [
            {"label": "Traditional IRA",   "category": "retirement",     "owner": "client1", "last4": "6603", "balance": 720000, "interest_rate": 0,    "address": ""},
            {"label": "Roth IRA",          "category": "retirement",     "owner": "client1", "last4": "1198", "balance": 88000,  "interest_rate": 0,    "address": ""},
            {"label": "Pension (vested)",  "category": "retirement",     "owner": "client1", "last4": "",     "balance": 310000, "interest_rate": 0,    "address": ""},
            {"label": "Schwab Brokerage",  "category": "non_retirement", "owner": "client1", "last4": "4450", "balance": 290000, "interest_rate": 0,    "address": ""},
            {"label": "Primary Residence", "category": "trust",          "owner": "client1", "last4": "",     "balance": 495000, "interest_rate": 0,    "address": "17 Cherokee Trail, Marietta, GA"},
            {"label": "Mortgage",          "category": "liability",      "owner": "client1", "last4": "",     "balance": 87000,  "interest_rate": 3.75, "address": ""},
        ],
    },
    quarters=[
        ("Q1 2026", {
            "Schwab Brokerage": 278000, "Traditional IRA": 708000,
        }),
        ("Q2 2026", {
            "Schwab Brokerage": 290000, "Traditional IRA": 720000,
        }),
    ],
)

print("\nAll demo clients seeded successfully.")
