"""
AW Client Report Portal — calculation engine.

All math for the SACS (cashflow) and TCC (net worth) reports lives here so it can
be unit-tested in isolation. The rules below are taken VERBATIM from the PRD and
the client call. Do not "improve" them — Rebecca was explicit:

  - Liabilities are NOT subtracted from net worth (shown in a separate box).
  - The trust is NOT added to the non-retirement total.
  - Non-retirement total = accounts only, never the trust.
"""
from datetime import date


def calculate_age(dob_iso: str | None) -> int | None:
    """Age from an ISO date string (YYYY-MM-DD)."""
    if not dob_iso:
        return None
    try:
        y, m, d = (int(x) for x in dob_iso.split("-"))
        born = date(y, m, d)
    except (ValueError, AttributeError):
        return None
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def _sum(accounts, **filters):
    total = 0.0
    for a in accounts:
        if all(a.get(k) == v for k, v in filters.items()):
            total += float(a.get("balance") or 0)
    return total


def compute_sacs(*, inflow, outflow, insurance_deductibles_total=0):
    """
    SACS (Simple Automated Cash Flow).
      Excess               = Inflow - Outflow
      Private Reserve Tgt   = (6 * monthly expenses) + sum(insurance deductibles)
    """
    inflow = float(inflow or 0)
    outflow = float(outflow or 0)
    deductibles = float(insurance_deductibles_total or 0)
    excess = inflow - outflow
    reserve_target = (6 * outflow) + deductibles
    return {
        "inflow": inflow,
        "outflow": outflow,
        "excess": excess,                       # goes to Private Reserve
        "reserve_target": reserve_target,
    }


def compute_tcc(accounts):
    """
    TCC (Total Client Chart) net-worth math.

    `accounts` is a list of dicts, each with:
        category: 'retirement' | 'non_retirement' | 'trust' | 'liability'
        owner:    'client1' | 'client2' | 'joint'   (for retirement split)
        balance:  number

    Returns the section totals. Liabilities are reported separately and are
    NEVER subtracted from net worth. Trust is part of net worth but NOT part of
    the non-retirement total.
    """
    c1_retirement = _sum(accounts, category="retirement", owner="client1")
    c2_retirement = _sum(accounts, category="retirement", owner="client2")
    non_retirement = _sum(accounts, category="non_retirement")
    trust = _sum(accounts, category="trust")
    liabilities = _sum(accounts, category="liability")

    grand_total = c1_retirement + c2_retirement + non_retirement + trust

    return {
        "c1_retirement_total": c1_retirement,
        "c2_retirement_total": c2_retirement,
        "non_retirement_total": non_retirement,   # excludes trust by design
        "trust_total": trust,
        "grand_total_net_worth": grand_total,      # liabilities NOT subtracted
        "liabilities_total": liabilities,          # separate box only
    }
