"""Unit tests for the calculation rules. Run: python -m pytest test_calculations.py
   (or just `python test_calculations.py`)."""
from calculations import compute_sacs, compute_tcc


def test_sacs_excess_and_target():
    r = compute_sacs(inflow=15000, outflow=11000, insurance_deductibles_total=2000)
    assert r["excess"] == 4000                 # 15000 - 11000
    assert r["reserve_target"] == 6 * 11000 + 2000   # 68000


def test_tcc_rules():
    accounts = [
        {"category": "retirement", "owner": "client1", "balance": 11000},   # IRA
        {"category": "retirement", "owner": "client1", "balance": 15000},   # Roth
        {"category": "retirement", "owner": "client2", "balance": 20000},
        {"category": "non_retirement", "owner": "joint", "balance": 50000},  # brokerage
        {"category": "trust", "owner": "joint", "balance": 450000},          # house
        {"category": "liability", "owner": "joint", "balance": 200000},      # mortgage
    ]
    t = compute_tcc(accounts)
    assert t["c1_retirement_total"] == 26000
    assert t["c2_retirement_total"] == 20000
    assert t["non_retirement_total"] == 50000          # trust NOT included
    assert t["trust_total"] == 450000
    # net worth = 26000 + 20000 + 50000 + 450000, liabilities NOT subtracted
    assert t["grand_total_net_worth"] == 546000
    assert t["liabilities_total"] == 200000


if __name__ == "__main__":
    test_sacs_excess_and_target()
    test_tcc_rules()
    print("All calculation tests passed ✓")
