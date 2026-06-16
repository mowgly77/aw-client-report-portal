"""
AW Client Report Portal — Flask app.

Flow:  Clients list -> add/edit client (static profile + account structure)
       -> Generate Report (enter quarterly balances) -> SACS & TCC PDFs.

Stack per PRD: Flask + SQLite + WeasyPrint. No API integrations, no AI in V1.
"""
import io
from datetime import date

from flask import Flask, abort, redirect, render_template, request, send_file, url_for

import db
from calculations import calculate_age, compute_sacs, compute_tcc

app = Flask(__name__)
db.init_db()

ACCOUNT_CATEGORIES = ["retirement", "non_retirement", "trust", "liability"]
ACCOUNT_OWNERS = ["client1", "client2", "joint"]


# ---- request parsing ------------------------------------------------------
def _f(name, default=0.0):
    """Parse a float form field, tolerating $ and commas and blanks."""
    raw = (request.form.get(name) or "").replace("$", "").replace(",", "").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _parse_accounts():
    """Reconstruct the account rows posted from the dynamic table."""
    accounts = []
    labels = request.form.getlist("acct_label")
    cats = request.form.getlist("acct_category")
    owners = request.form.getlist("acct_owner")
    last4 = request.form.getlist("acct_last4")
    balances = request.form.getlist("acct_balance")
    rates = request.form.getlist("acct_rate")
    addrs = request.form.getlist("acct_address")
    def num(lst, idx):
        v = (lst[idx] if idx < len(lst) else "").replace("$", "").replace(",", "").strip()
        try:
            return float(v)
        except (ValueError, AttributeError):
            return 0.0

    for i in range(len(labels)):
        label = (labels[i] or "").strip()
        if not label:
            continue
        accounts.append({
            "label": label,
            "category": cats[i] if i < len(cats) else "non_retirement",
            "owner": owners[i] if i < len(owners) else "joint",
            "last4": (last4[i] if i < len(last4) else "").strip(),
            "balance": num(balances, i),
            "interest_rate": num(rates, i),
            "address": (addrs[i] if i < len(addrs) else "").strip(),
        })
    return accounts


# ---- routes ---------------------------------------------------------------
@app.route("/")
def index():
    clients = db.list_clients()
    for c in clients:
        c["age1"] = calculate_age(c.get("dob1"))
    return render_template("clients_list.html", clients=clients)


@app.route("/client/new", methods=["GET", "POST"])
@app.route("/client/<int:client_id>/edit", methods=["GET", "POST"])
def client_form(client_id=None):
    client = db.get_client(client_id) if client_id else None
    if request.method == "POST":
        data = {
            "is_married": 1 if request.form.get("is_married") else 0,
            "name1": request.form.get("name1", "").strip(),
            "dob1": request.form.get("dob1") or None,
            "ssn1_last4": request.form.get("ssn1_last4", "").strip(),
            "name2": request.form.get("name2", "").strip(),
            "dob2": request.form.get("dob2") or None,
            "ssn2_last4": request.form.get("ssn2_last4", "").strip(),
            "monthly_salary": _f("monthly_salary"),
            "monthly_expense_budget": _f("monthly_expense_budget"),
            "insurance_deductibles_total": _f("insurance_deductibles_total"),
            "private_reserve_balance": _f("private_reserve_balance"),
            "schwab_balance": _f("schwab_balance"),
            "accounts": _parse_accounts(),
        }
        new_id = db.save_client(data, client_id)
        return redirect(url_for("report_form", client_id=new_id))
    return render_template(
        "client_form.html",
        client=client,
        categories=ACCOUNT_CATEGORIES,
        owners=ACCOUNT_OWNERS,
    )


@app.route("/client/<int:client_id>/report", methods=["GET", "POST"])
def report_form(client_id):
    client = db.get_client(client_id)
    if not client:
        abort(404)
    if request.method == "POST":
        # Persist freshly entered balances back onto the client, then snapshot.
        client["private_reserve_balance"] = _f("private_reserve_balance")
        client["schwab_balance"] = _f("schwab_balance")
        client["monthly_salary"] = _f("monthly_salary")
        client["monthly_expense_budget"] = _f("monthly_expense_budget")
        client["insurance_deductibles_total"] = _f("insurance_deductibles_total")
        client["accounts"] = _parse_accounts()
        db.save_client(client, client_id)
        snap = _build_report(client)
        db.save_report(client_id, request.form.get("quarter_label", ""), snap)
        return redirect(url_for("report_view", client_id=client_id))
    return render_template(
        "report_form.html",
        client=client,
        categories=ACCOUNT_CATEGORIES,
        owners=ACCOUNT_OWNERS,
    )


def _build_report(client):
    sacs = compute_sacs(
        inflow=client.get("monthly_salary"),
        outflow=client.get("monthly_expense_budget"),
        insurance_deductibles_total=client.get("insurance_deductibles_total"),
    )
    tcc = compute_tcc(client.get("accounts", []))
    return {
        "client": client,
        "sacs": sacs,
        "tcc": tcc,
        "report_date": date.today().isoformat(),
    }


@app.route("/client/<int:client_id>/report/view")
def report_view(client_id):
    client = db.get_client(client_id)
    if not client:
        abort(404)
    ctx = _build_report(client)
    return render_template("report_view.html", **ctx)


def _render_pdf(template, **ctx):
    from weasyprint import HTML
    html = render_template(template, **ctx)
    pdf = HTML(string=html, base_url=request.base_url).write_pdf()
    return io.BytesIO(pdf)


@app.route("/client/<int:client_id>/pdf/<kind>")
def pdf(client_id, kind):
    client = db.get_client(client_id)
    if not client or kind not in ("sacs", "tcc"):
        abort(404)
    ctx = _build_report(client)
    buf = _render_pdf(f"pdf_{kind}.html", **ctx)
    fname = f"{client['name1'].split(' ')[0]}_{kind.upper()}_{ctx['report_date']}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=fname)


@app.template_filter("money")
def money(value):
    try:
        return f"${float(value or 0):,.0f}"
    except (ValueError, TypeError):
        return "$0"


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
