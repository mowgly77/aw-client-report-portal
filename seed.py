"""Load one sample married client so you can demo immediately. Run: python seed.py"""
import db

db.init_db()
db.save_client({
    "is_married": 1,
    "name1": "Andrew Whitfield", "dob1": "1972-05-14", "ssn1_last4": "4821",
    "name2": "Rebecca Whitfield", "dob2": "1975-09-02", "ssn2_last4": "7390",
    "monthly_salary": 15000,
    "monthly_expense_budget": 11000,
    "insurance_deductibles_total": 6500,
    "private_reserve_balance": 72000,
    "schwab_balance": 318000,
    "accounts": [
        {"label": "Traditional IRA", "category": "retirement", "owner": "client1", "last4": "1102", "balance": 240000, "interest_rate": 0, "address": ""},
        {"label": "Roth IRA", "category": "retirement", "owner": "client1", "last4": "8847", "balance": 95000, "interest_rate": 0, "address": ""},
        {"label": "401(k)", "category": "retirement", "owner": "client2", "last4": "3310", "balance": 410000, "interest_rate": 0, "address": ""},
        {"label": "Joint Brokerage (Schwab)", "category": "non_retirement", "owner": "joint", "last4": "5521", "balance": 318000, "interest_rate": 0, "address": ""},
        {"label": "Primary Residence", "category": "trust", "owner": "joint", "last4": "", "balance": 845000, "interest_rate": 0, "address": "418 Peachtree Ln, Atlanta, GA"},
        {"label": "Mortgage", "category": "liability", "owner": "joint", "last4": "", "balance": 286000, "interest_rate": 5.25, "address": ""},
        {"label": "Auto Loan", "category": "liability", "owner": "joint", "last4": "", "balance": 24000, "interest_rate": 6.9, "address": ""},
    ],
})
print("Seeded sample client ✓")
