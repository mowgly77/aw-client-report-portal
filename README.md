# AW Client Report Portal

Web portal for a financial planning firm to enter client data once, then generate
polished quarterly **SACS** (cashflow) and **TCC** (net worth) PDF reports in minutes.

Stack (per PRD): **Flask + SQLite + WeasyPrint**. No external APIs, no AI in V1.

## What it does
- **Client profiles** — static info entered once (names, DOB, age auto, last-4 SSN, account structure, salary, expense budget, reserve target). Single or married (Client 1 / Client 2).
- **Quarterly entry** — pre-fills static data, you enter current balances; all totals recalc live.
- **Auto calculations** (exact rules from the call):
  - Excess = Inflow − Outflow
  - Reserve target = (6 × monthly expenses) + insurance deductibles
  - Net worth = C1 retirement + C2 retirement + non-retirement + trust
  - Liabilities shown **separately**, never subtracted; trust **never** in non-retirement total
- **PDF generation** — SACS cashflow diagram + TCC net-worth chart, fixed layout, download-ready.

## Run locally
```bash
pip install -r requirements.txt          # needs system Pango/Cairo for WeasyPrint
python seed.py        # optional: loads one sample married client
python app.py         # http://localhost:5000
```
On macOS, WeasyPrint needs: `brew install pango gdk-pixbuf libffi`

## Run with Docker (recommended — same image local & prod)
```bash
docker compose up --build      # http://localhost:8000
```
The `Dockerfile` bundles the Pango/Cairo libraries WeasyPrint needs, so there's nothing
to install on your machine. Railway builds from this same Dockerfile (`railway.json`).

## Tests & lint
```bash
pip install -r requirements-dev.txt
ruff check .          # lint
pytest                # unit (calculations) + integration (routes + PDF rendering)
```

## CI/CD (GitHub Actions)
- `.github/workflows/ci.yml` — runs ruff + pytest on every push and PR.
- `.github/workflows/deploy.yml` — deploys to Railway on merge to `main`.

One-time setup for auto-deploy:
1. Railway → Project → Settings → Tokens → create a token.
2. GitHub repo → Settings → Secrets and variables → Actions → add secret `RAILWAY_TOKEN`.
3. (Optional) add repo variable `RAILWAY_SERVICE` if your service isn't named `web`.

## Deploy to Railway (manual, first time)
1. Push this folder to a GitHub repo.
2. Railway → New Project → Deploy from GitHub repo.
3. Railway auto-detects Nixpacks; `nixpacks.toml` installs the Pango/Cairo libs and
   `Procfile` starts gunicorn. No build config needed.
4. (Optional) Add a Railway Volume and set `RAILWAY_DATABASE_PATH=/data/portal.db`
   so the SQLite file persists across deploys.

## Files
- `app.py` — routes, form parsing, PDF rendering
- `calculations.py` — all math (unit-tested in `test_calculations.py`)
- `db.py` — SQLite storage
- `templates/` — UI pages + `pdf_sacs.html` / `pdf_tcc.html` report templates
- `static/style.css` — portal styling

## Out of V1 scope (future)
Canva export, Dropbox auto-save, and auto-pull from RightCapital / Schwab / Pinnacle / Zillow
were deferred per the call — V1 is manual entry only, by design.
