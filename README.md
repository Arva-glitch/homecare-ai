# Smart Household Maintenance Manager – Predictive HomeCare AI

A full-stack web application that helps a household track its appliances, predict which ones need maintenance,
schedule servicing, report problems, track expenses, and get help from an AI assistant.

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Tailwind CSS, Recharts, Lucide React, Axios, React Router |
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2, Pydantic 2, JWT (python-jose), bcrypt (passlib) |
| Database | MySQL 8 / MariaDB 10.6+, Alembic migrations |
| AI / ML | scikit-learn Random Forest, pandas, NumPy, rule-based fallback, LLM assistant (Anthropic or OpenAI-compatible) with a rule-based fallback |
| Testing | Pytest (36 backend unit + API integration tests), Vitest + Testing Library (frontend), Playwright end-to-end script |

> **About the predictions:** no real appliance-failure dataset was available, so the model is trained on a
> **clearly labelled synthetic dataset** (`backend/app/ml/synthetic_data.py`). Its scores are
> maintenance-priority estimates, **not** validated real-world failure probabilities. The UI and API say so.

---

## Demo credentials

| Account | Email | Password |
|---|---|---|
| Main demo household (7 appliances, history, expenses, issues, schedules, predictions, chat) | `demo@homecare.ai` | `Demo@1234` |
| Second household (shows that users only see their own data) | `priya@homecare.ai` | `Demo@1234` |

These are created by `python seed.py` and are for demonstration only.

---

## Quick start

### Prerequisites
* Python 3.10+ · Node.js 18+ · MySQL 8 (or MariaDB 10.6+)

### 1. Database
```sql
CREATE DATABASE homecare_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'homecare'@'localhost' IDENTIFIED BY 'homecare_pass';
GRANT ALL PRIVILEGES ON homecare_db.* TO 'homecare'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate     macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env  — then edit DATABASE_URL / SECRET_KEY
alembic upgrade head          # create the 9 tables
python -m app.ml.train        # train the Random Forest on synthetic data (also happens automatically on first start)
python seed.py                # load demo users and data (use --reset to recreate)
uvicorn app.main:app --reload --port 8000
```
API: http://localhost:8000 · Swagger: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173 and click **Fill demo login**. The Vite dev server proxies `/api` and `/uploads` to port 8000.

Production build: `npm run build` (output in `frontend/dist`). If the frontend is hosted on a different origin, set
`VITE_API_BASE_URL` (see `frontend/.env.example`) and add that origin to `CORS_ORIGINS` in `backend/.env`.

### Optional features
| Feature | How to enable | Without it |
|---|---|---|
| LLM-powered assistant & issue suggestions | Set `LLM_API_KEY` (and `LLM_PROVIDER=anthropic` or `openai`, optional `LLM_MODEL`, `LLM_BASE_URL`) in `backend/.env` | Built-in rule-based NLU + troubleshooting knowledge base |
| Email (password reset links, critical alerts) | Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` | Reset link shown in the UI in development mode; in-app alerts only |

---

## Testing

```bash
# Backend: unit + API integration tests (uses a temporary SQLite DB by default)
cd backend && pytest
# Run the same tests against MySQL:
TEST_DATABASE_URL=mysql+pymysql://homecare:homecare_pass@localhost:3306/homecare_test pytest

# Frontend component/unit tests
cd frontend && npm test

# End-to-end UI test (backend + frontend running, demo data seeded; needs Chrome)
cd frontend && npm i -D playwright-core && node e2e/e2e.mjs
```

| Suite | File | Covers |
|---|---|---|
| Authentication | `tests/test_auth.py` | register, login, hashing, duplicate email, weak password, protected routes, logout revocation, forgot/reset password (single-use token), profile + password change |
| Appliance CRUD | `tests/test_appliances.py` | create (auto-prediction), list/search/filter/sort, update, delete, validation, cross-user isolation, image upload validation, maintenance records → expenses |
| Scheduling | `tests/test_schedules.py` | CRUD, views, status transitions, completion → record + expense + re-prediction, cancel, isolation, AI suggestions accept |
| Predictive model | `tests/test_predictive.py` | rule scoring, critical override, synthetic dataset, training beats chance, ML + fallback paths, feature extraction, prediction API, issue → risk update |
| Other modules | `tests/test_modules.py` | expenses + reports, notifications (idempotent), chatbot (all sample questions), dashboard from DB, per-user dashboard |
| Frontend | `frontend/src/__tests__` | formatting utils, badges, markdown renderer, confirm dialog, calendar |
| E2E | `frontend/e2e/e2e.mjs` | 13 user journeys across every page in a real browser, incl. mobile layout |

Verified results: **36/36 backend tests on SQLite and on MySQL (MariaDB 10.11)**, 10/10 frontend tests, 13/13 E2E journeys with 0 console/API errors.

---

## Project structure
```
homecare-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, error handlers, router registration
│   │   ├── core/                # config.py (env settings), security.py (bcrypt/JWT), deps.py (auth & ownership)
│   │   ├── db/                  # base.py (Base + timestamps), session.py (engine/session)
│   │   ├── models/              # 9 SQLAlchemy models + enums
│   │   ├── schemas/             # Pydantic request/response schemas with validation
│   │   ├── routers/             # auth, users, dashboard, appliances, predictions, schedules, issues, expenses, notifications, chat, meta
│   │   ├── services/            # prediction, notification, chat, knowledge_base, llm_client, serializers
│   │   ├── ml/                  # features.py, synthetic_data.py, train.py, predictor.py, artifacts/
│   │   └── utils/               # files.py (uploads), email.py (SMTP), time.py
│   ├── alembic/                 # migration environment + versions/0001_initial_schema.py
│   ├── tests/                   # pytest suites
│   ├── seed.py                  # demo data
│   ├── requirements.txt · .env.example · alembic.ini · pytest.ini
├── frontend/
│   ├── src/
│   │   ├── api/                 # axios client + service functions
│   │   ├── context/             # Auth, Toast, Options providers
│   │   ├── components/          # Layout (sidebar), ui kit, forms, calendar
│   │   ├── pages/               # one file per screen
│   │   ├── utils/ · hooks.js · __tests__/
│   ├── e2e/e2e.mjs
│   ├── package.json · vite.config.js · tailwind.config.js · .env.example
└── docs/
    ├── ARCHITECTURE.md          # architecture + sequence diagrams
    ├── DATABASE.md              # ER diagram, tables, indexes
    ├── API.md · openapi.json    # endpoint reference (60 endpoints)
    └── schema.sql               # MySQL DDL generated from the migration
```

---

## Modules

Each module below lists the files, what it does, how to try it, and its dependencies.

### 1. Authentication & profile
* **Files:** `core/security.py`, `core/deps.py`, `routers/auth.py`, `routers/users.py`, `schemas/auth.py`, `pages/Auth.jsx`, `pages/Profile.jsx`, `context/AuthContext.jsx`
* **Features:** registration with password rules, bcrypt hashing, JWT login, server-side logout (token versioning), safe forgot/reset password (hashed, expiring, single-use token, no account enumeration), profile editing, password change, email-alert preference.
* **Try it:** register a new account; use *Forgot password* (the reset link appears on screen when SMTP is off).
* **Deps:** python-jose, passlib, bcrypt, email-validator.

### 2. Dashboard
* **Files:** `routers/dashboard.py`, `pages/Dashboard.jsx`, `components/MiniCalendar.jsx`
* **Features:** totals for appliances, appliances needing maintenance, upcoming/overdue/completed tasks, total expenses; monthly-expense bar chart; risk-distribution donut; per-appliance health bars; AI alerts; calendar; recent-activity feed. Every number comes from one `/api/dashboard/summary` query set — nothing is hard-coded.

### 3. Appliance management
* **Files:** `models/appliance.py`, `routers/appliances.py`, `pages/Appliances.jsx`, `pages/ApplianceDetail.jsx`, `components/ApplianceForm.jsx`, `utils/files.py`
* **Features:** add/edit/delete with all required fields (8 categories), validated image upload, search (name/brand/model), filter (category/risk/condition), 7 sort options, detail page with maintenance history (add/delete records), health trend chart and latest explanation.

### 4. Predictive maintenance AI (core)
* **Files:** `ml/features.py`, `ml/synthetic_data.py`, `ml/train.py`, `ml/predictor.py`, `services/prediction_service.py`, `routers/predictions.py`, `pages/Predictions.jsx`
* **Inputs:** age, expected lifespan, usage frequency, time since last service vs. category interval, services in the last 2 years, previous breakdowns, open reported problems and their severity, condition.
* **Outputs:** health score 0–100, risk level (Low/Medium/High/Critical), maintenance priority, recommended service date, explanation (top factors with point impacts), class probabilities, model confidence.
* **Model:** `RandomForestClassifier` (200 trees) trained on 6,000 synthetic rows labelled by a noisy heuristic with interaction effects. Hold-out accuracy on synthetic data ≈ 73% (macro-F1 ≈ 0.74). This measures how well it learned the heuristic, not real-world accuracy.
* **Fallback:** transparent rule engine (point deductions) used if the model can't load; a safety rule keeps any appliance with an open *Critical* issue at High risk or above.
* **Triggers:** runs automatically when an appliance is created or edited, when maintenance is logged or completed, and when issues are reported, updated or deleted. Can also be run on demand. Full history is kept in `prediction_history`.

### 5. AI HomeCare Assistant
* **Files:** `services/chat_service.py`, `services/knowledge_base.py`, `services/llm_client.py`, `routers/chat.py`, `pages/Assistant.jsx`
* **Features:** chat with saved conversations; builds context from the user's appliances, health, risk, schedules and open issues. With `LLM_API_KEY` set it calls the LLM using a safety-focused system prompt; otherwise (or if the call fails) it uses intent detection + a troubleshooting knowledge base for 7 categories. It handles all six example questions, gives appliance-specific advice (risk, warranty), phrases causes as possibilities, and recommends professionals for safety-critical work.

### 6. Maintenance scheduling
* **Files:** `models/maintenance.py`, `routers/schedules.py`, `pages/Scheduler.jsx`, `components/ScheduleForm.jsx`
* **Features:** create/edit/cancel/restore/delete, statuses Pending → Scheduled → In Progress → Completed / Cancelled with validated transitions, upcoming/overdue/completed/cancelled tabs, calendar, AI-suggested schedules from predictions (one-click accept). Completing a task writes history, logs the expense and re-scores the appliance.

### 7. Issue reporting
* **Files:** `models/issue.py`, `routers/issues.py`, `pages/Issues.jsx`
* **Features:** appliance, category, description, severity, date, optional photo; P1–P4 priority; AI troubleshooting suggestions; immediate risk re-assessment; recommended service you can schedule in one click; status tracking.

### 8. Expense tracking
* **Files:** `models/expense.py`, `routers/expenses.py`, `pages/Expenses.jsx`
* **Features:** CRUD with repair/servicing/replacement/parts/other types, optional appliance link, filters; total, yearly, monthly (stacked by type) and by-type reports; appliance-wise totals; highest-cost appliance.

### 9. Notifications & alerts
* **Files:** `services/notification_service.py`, `routers/notifications.py`, `pages/Notifications.jsx`, `utils/email.py`
* **Alerts:** upcoming servicing (7 days), warranty expiring (30 days) or just expired, High/Critical-risk appliances, overdue or pending maintenance, open critical issues. Alerts are de-duplicated. The notification centre supports read/unread, mark-all-read, delete and type filters, and the sidebar shows an unread badge. Critical alerts are emailed if SMTP is configured and the user opted in.

---

## API documentation
FastAPI generates Swagger at `/docs`. A static endpoint reference is in [`docs/API.md`](docs/API.md).

## Diagrams
* Software architecture and sequence diagrams: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
* ER diagram and schema documentation: [`docs/DATABASE.md`](docs/DATABASE.md) · DDL: [`docs/schema.sql`](docs/schema.sql)

(Diagrams are Mermaid. They render on GitHub and in VS Code with a Mermaid extension, or paste them into https://mermaid.live to export PNG/SVG.)

## Troubleshooting
| Problem | Fix |
|---|---|
| `Access denied for user` / can't connect | Check `DATABASE_URL` in `backend/.env` and that MySQL is running |
| `cryptography package is required` | `pip install cryptography` (MySQL 8 authentication) |
| bcrypt `__about__` error | `pip install bcrypt==4.0.1` |
| Frontend shows "Cannot reach the server" | Start the backend on port 8000, or set `VITE_PROXY_TARGET` / `VITE_API_BASE_URL` |
| Model trained with a different scikit-learn version | Nothing to do: the backend retrains automatically on start (or run `python -m app.ml.train`) |
