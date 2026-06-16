"""Integration tests: the app boots, routes respond, and both PDFs render via WeasyPrint."""
import os
import tempfile

import pytest

# Use a throwaway DB so tests never touch a real portal.db.
os.environ["RAILWAY_DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "test_portal.db")
if os.path.exists(os.environ["RAILWAY_DATABASE_PATH"]):
    os.remove(os.environ["RAILWAY_DATABASE_PATH"])

import app as app_module  # noqa: E402  (import after env is set)
import db  # noqa: E402


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture()
def sample_client_id():
    return db.save_client({
        "is_married": 1,
        "name1": "Test One", "dob1": "1980-01-01", "ssn1_last4": "1111",
        "name2": "Test Two", "dob2": "1982-02-02", "ssn2_last4": "2222",
        "monthly_salary": 15000, "monthly_expense_budget": 11000,
        "insurance_deductibles_total": 2000,
        "private_reserve_balance": 70000, "schwab_balance": 300000,
        "accounts": [
            {"label": "IRA", "category": "retirement", "owner": "client1", "last4": "1", "balance": 100000, "interest_rate": 0, "address": ""},
            {"label": "401k", "category": "retirement", "owner": "client2", "last4": "2", "balance": 200000, "interest_rate": 0, "address": ""},
            {"label": "Brokerage", "category": "non_retirement", "owner": "joint", "last4": "3", "balance": 50000, "interest_rate": 0, "address": ""},
            {"label": "House", "category": "trust", "owner": "joint", "last4": "", "balance": 450000, "interest_rate": 0, "address": "1 Main St"},
            {"label": "Mortgage", "category": "liability", "owner": "joint", "last4": "", "balance": 200000, "interest_rate": 5.0, "address": ""},
        ],
    })


def test_index_loads(client):
    assert client.get("/").status_code == 200


def test_report_pages_load(client, sample_client_id):
    assert client.get(f"/client/{sample_client_id}/report").status_code == 200
    assert client.get(f"/client/{sample_client_id}/report/view").status_code == 200


def test_sacs_pdf_renders(client, sample_client_id):
    r = client.get(f"/client/{sample_client_id}/pdf/sacs")
    assert r.status_code == 200
    assert r.data[:4] == b"%PDF"
    assert r.headers["Content-Type"] == "application/pdf"


def test_tcc_pdf_renders(client, sample_client_id):
    r = client.get(f"/client/{sample_client_id}/pdf/tcc")
    assert r.status_code == 200
    assert r.data[:4] == b"%PDF"


def test_net_worth_in_view(client, sample_client_id):
    # 100k + 200k + 50k + 450k = 800k, liabilities (200k) NOT subtracted.
    html = client.get(f"/client/{sample_client_id}/report/view").get_data(as_text=True)
    assert "$800,000" in html


def test_unknown_pdf_kind_404(client, sample_client_id):
    assert client.get(f"/client/{sample_client_id}/pdf/bogus").status_code == 404


def test_create_client_via_form(client):
    r = client.post("/client/new", data={
        "name1": "Form Client", "monthly_salary": "12000",
        "monthly_expense_budget": "9000", "insurance_deductibles_total": "1000",
        "private_reserve_balance": "50000", "schwab_balance": "120000",
        "acct_label": "Roth", "acct_category": "retirement", "acct_owner": "client1",
        "acct_last4": "9", "acct_balance": "80000", "acct_rate": "", "acct_address": "",
    }, follow_redirects=False)
    assert r.status_code in (301, 302)  # redirects to the report form
