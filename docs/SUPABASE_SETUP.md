# Supabase Setup Guide — SafePlant AI

**Your project:** `recpimnzdordbuiwypgp`
**Your URL:** `https://recpimnzdordbuiwypgp.supabase.co`

---

## What You Have vs What You Need

| Credential | Value | Used For |
|---|---|---|
| **Supabase URL** | `https://recpimnzdordbuiwypgp.supabase.co` | Supabase API / client |
| **Anon Key** (provided) | `eyJhbGci…` | Supabase REST API / Auth |
| **DB Password** ⚠️ NEEDED | `[set during project creation]` | SQLAlchemy direct PostgreSQL connection |

> The **anon key** is a JWT for Supabase's REST API.
> The **DB password** is the PostgreSQL `postgres` user password — these are **different**.

---

## Step 1 — Get Your Database Password

1. Go to **https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/settings/database**
2. Scroll to **"Database password"** section
3. Click **"Reset database password"** if you don't remember it
4. Copy the new password

---

## Step 2 — Configure `.env`

Edit `backend/.env` — replace `YOUR-DB-PASSWORD`:

```env
# Direct connection (Session Pooler — recommended)
DATABASE_URL=postgresql://postgres:YOUR-DB-PASSWORD@db.recpimnzdordbuiwypgp.supabase.co:5432/postgres

# ↑ Only change YOUR-DB-PASSWORD, everything else is already correct.
```

**Full `.env` example:**
```env
DATABASE_URL=postgresql://postgres:MyStr0ngP@$$@db.recpimnzdordbuiwypgp.supabase.co:5432/postgres
SUPABASE_URL=https://recpimnzdordbuiwypgp.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlY3BpbW56ZG9yZGJ1aXd5cGdwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTMwODg4OTgsImV4cCI6MjEwODY2NDg5OH0.b4ak22ywyuCjaApPsq4dud5FahsNmXdb0RyG-qR7VtQ
SECRET_KEY=safeplant-dev-secret-min-32-chars
FLASK_ENV=development
FLASK_DEBUG=1
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
DATA_DIR=../data
GENERATION_SEED=20261022
```

---

## Step 3 — Install Python Dependencies

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 4 — Create All 20 Tables in Supabase

```powershell
# One-time setup: initialise Alembic migration folder
flask db init

# Generate migration script from SQLAlchemy models
flask db migrate -m "SafePlant AI initial schema"

# Apply to Supabase PostgreSQL → creates all 20 tables
flask db upgrade
```

After this, check **Supabase → Table Editor** — you should see:

| Core Tables (10) | Supporting Tables (10) |
|---|---|
| `plant` | `machine_safety_zone` |
| `machine` | `machine_interlock` |
| `safety_zone` | `machine_state_event` |
| `interlock` | `interlock_state_event` |
| `alarm_definition` | `incident_alarm` |
| `alarm_event` | `incident_state_event` |
| `operator_shift` | `corrective_action_event` |
| `acknowledgement` | `audit_log` |
| `incident` | `generation_run` |
| `corrective_action` | `validation_run` |

---

## Step 5 — Generate Synthetic Data

```powershell
# Starter (fast ~30 seconds, ~50 MB)
python scripts/generate_data.py --mode starter --seed 20261022 --validate

# Full (takes 3-5 min, ~500 MB)
python scripts/generate_data.py --mode full --seed 20261022 --validate
```

Or use the UI: **http://localhost:5173** → **Data Generator** → Run Starter Generation

---

## Step 6 — Start Everything

**Terminal 1 (Backend):**
```powershell
cd backend
venv\Scripts\activate
python run.py
# API running at http://localhost:5000
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
# UI running at http://localhost:5173
```

---

## Connection Modes

| Mode | Port | URL Format |
|------|------|-----------|
| **Session Pooler** ✅ (recommended) | 5432 | `db.recpimnzdordbuiwypgp.supabase.co:5432` |
| Transaction Pooler | 6543 | `aws-0-[region].pooler.supabase.com:6543` |

The app auto-sets `sslmode=require` — no extra configuration needed.

---

## Troubleshooting

### ❌ "password authentication failed for user postgres"
→ Wrong DB password. Go to **Settings → Database → Reset password**, copy new password, update `.env`

### ❌ Connection timeout
→ Try the Transaction Pooler URL (port 6543):
```env
DATABASE_URL=postgresql://postgres.recpimnzdordbuiwypgp:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

### ❌ SSL error
→ Do NOT disable SSL. The config already sets `sslmode=require` which is correct.

### ❌ "no such table" after flask db upgrade
→ Run `flask db current` to check state, then `flask db upgrade` again

---

## Supabase Dashboard Quick Links

| Page | URL |
|------|-----|
| **Database password** | https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/settings/database |
| **Table editor** | https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/editor |
| **SQL editor** | https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/sql/new |
| **Logs** | https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/logs/postgres-logs |
| **API keys** | https://supabase.com/dashboard/project/recpimnzdordbuiwypgp/settings/api |
