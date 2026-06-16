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
import validators as V
from calculations import calculate_age, compute_sacs, compute_tcc

app = Flask(__name__)
db.init_db()

ACCOUNT_CATEGORIES = list(V.ACCOUNT_CATEGORIES)
ACCOUNT_OWNERS = list(V.ACCOUNT_OWNERS)


# ---- request parsing ------------------------------------------------------
def _f(name: str, default: float = 0.0) -> float:
    """Lenient float parse (used for the report form, where 0 is valid)."""
    raw = (request.form.get(name) or "").replace("$", "").replace(",", "").strip()
    if raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _parse_accounts(errors: list[str] | None = None) -> list[dict]:
    """Reconstruct + validate the account rows posted from the dynamic table.

    Category/owner are whitelisted, last-4 is digits-only, balances and rates are
    properly typed and range-checked. Rows without a label are ignored.
    """
    errors = errors if errors is not None else []
    accounts: list[dict] = []
    labels = request.form.getlist("acct_label")
    cats = request.form.getlist("acct_category")
    owners = request.form.getlist("acct_owner")
    last4 = request.form.getlist("acct_last4")
    balances = request.form.getlist("acct_balance")
    rates = request.form.getlist("acct_rate")
    addrs = request.form.getlist("acct_address")

    def at(lst: list[str], idx: int) -> str:
        return lst[idx] if idx < len(lst) else ""

    for i in range(len(labels)):
        label = V.clean_text(at(labels, i))
        if not label:
            continue
        bal = V.parse_money(at(balances, i), field=f"Balance de «{label}»", errors=errors)
        accounts.append({
            "label": label,
            "category": V.normalize_category(at(cats, i)),
            "owner": V.normalize_owner(at(owners, i)),
            "last4": V.digits_only(at(last4, i), max_len=4),
            "balance": bal if bal is not None else 0.0,
            "interest_rate": V.parse_rate(at(rates, i)),
            "address": V.clean_text(at(addrs, i), max_len=200),
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
        errors: list[str] = []
        is_married = 1 if request.form.get("is_married") else 0
        name1 = V.clean_text(request.form.get("name1"))
        if not name1:
            errors.append("El nombre del Cliente 1 es obligatorio.")
        data = {
            "is_married": is_married,
            "name1": name1,
            "dob1": V.parse_date(request.form.get("dob1"), field="Fecha de nacimiento (C1)", errors=errors),
            "ssn1_last4": V.digits_only(request.form.get("ssn1_last4"), max_len=4),
            "name2": V.clean_text(request.form.get("name2")),
            "dob2": V.parse_date(request.form.get("dob2"), field="Fecha de nacimiento (C2)", errors=errors),
            "ssn2_last4": V.digits_only(request.form.get("ssn2_last4"), max_len=4),
            "monthly_salary": V.parse_money(request.form.get("monthly_salary"), field="Inflow", errors=errors) or 0.0,
            "monthly_expense_budget": V.parse_money(request.form.get("monthly_expense_budget"), field="Outflow", errors=errors) or 0.0,
            "insurance_deductibles_total": V.parse_money(request.form.get("insurance_deductibles_total"), field="Deducibles", errors=errors) or 0.0,
            "private_reserve_balance": _f("private_reserve_balance"),
            "schwab_balance": _f("schwab_balance"),
            "accounts": _parse_accounts(errors),
        }
        if errors:
            return render_template(
                "client_form.html", client=data, errors=errors,
                categories=ACCOUNT_CATEGORIES, owners=ACCOUNT_OWNERS,
            ), 400
        new_id = db.save_client(data, client_id)
        return redirect(url_for("report_form", client_id=new_id))
    return render_template(
        "client_form.html",
        client=client,
        errors=[],
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
