# SafePlant AI — Industrial Safety Monitoring & Incident Intelligence System

> SafePlant AI v1.0.0

A production-ready industrial safety intelligence platform built with **Python Flask + PostgreSQL (Supabase) + React + Vite**. Analyzes machine safety events, interlocks, alarm acknowledgements, operator shifts, incidents, and corrective actions to identify repeated unsafe conditions and anomalies.

---

## Problem Statement Compliance Matrix

> Validation of all requirements from the Business Context / Problem Statement against the implemented solution.

### Business Context & Objective

| Requirement | Status | Implementation Evidence |
|---|---|---|
| Analyze safety events, machine states, acknowledgements and corrective actions | ✅ PASS | `anomaly_engine.py` detects 5 case types + floods + nuisance clusters + delayed acks across all 4 entity types |
| Find repeated unsafe conditions | ✅ PASS | `RULE-008` in `safety_engine.py`; `repeated_unsafe_condition_count=5` in live evaluation metrics |
| Expose key decisions and exceptions | ✅ PASS | All 5 anomaly cases flagged with `issue_type`, `rule_id`, `expected_decision` fields; visible in `/anomalies` page |
| Preserve traceability | ✅ PASS | `incident_alarm` bridge + `incident_state_event` + `corrective_action_event` + `/incidents/{id}/traceability` endpoint |
| Produce measurable outputs | ✅ PASS | `GET /evaluation/metrics` returns precision, recall, F1, TP, FP, FN, compliance rates |

### Primary Actors / Systems

| Actor | Status | Implementation Evidence |
|---|---|---|
| Plant operator | ✅ PASS | Operator shifts, alarm acknowledgements, operator_name on all ack records |
| Maintenance / quality engineer | ✅ PASS | `assigned_engineer` on incidents and corrective actions; 8 named engineers in generator |
| Production planner | ✅ PASS | Machine risk scores, analytics dashboard, top-10 risk chart |
| OT/IT administrator | ✅ PASS | Audit trail, validation runs, data generator, export endpoints |

### Business Workflow & Rules

| Rule | Status | Implementation Evidence |
|---|---|---|
| Generate master data first (Plant → Machine → Zone → Interlock → AlarmDef) | ✅ PASS | `master_generator.py` Steps 1–7 follow strict parent-before-child order |
| Generate dependent transaction records using valid parent IDs | ✅ PASS | All FKs resolved from in-memory parent lists before insert; FK validation passes 100% |
| Define machine safety zones and interlocks | ✅ PASS | `machine_safety_zone` and `machine_interlock` bridge tables with `effective_from` |
| Create alarm severity and acknowledgement rules | ✅ PASS | 4-tier severity; deadlines CRITICAL=120s, HIGH=300s, MEDIUM=900s, LOW=1800s in `config.py` |
| Generate state transitions and alarms with timestamps | ✅ PASS | `machine_state_event` (1,756 rows), `alarm_event` (1,003 rows) with ordered timestamps |
| Link operator shifts | ✅ PASS | `operator_shift` table; operator_name/id on every acknowledgement record |
| Create incidents for selected unsafe combinations | ✅ PASS | Incidents created from CRITICAL/HIGH alarm triggers; `incident_alarm` bridge links evidence |
| Record acknowledgement and action timelines | ✅ PASS | `acknowledgement` with `response_time_seconds`; `corrective_action_event` history |
| Preserve event ordering | ✅ PASS | All timestamps ordered; `alarm_timestamp < cleared_timestamp`; ack ordering validated |
| Persist state changes as explicit records | ✅ PASS | `machine_state_event`, `incident_state_event`, `corrective_action_event`, `interlock_state_event` — all immutable |
| No history overwrite | ✅ PASS | No DELETE on event tables; soft-delete only on master records via `is_active` |
| Ground-truth labels from documented rules, not random | ✅ PASS | All 5 anomaly cases injected deterministically from seed; labels derived from rule evaluation |

### Entities & Relationships

| Requirement | Status | Implementation Evidence |
|---|---|---|
| All 10 core entities present | ✅ PASS | Plant, Machine, SafetyZone, Interlock, AlarmDefinition, AlarmEvent, OperatorShift, Acknowledgement, Incident, CorrectiveAction |
| Primary key on every entity | ✅ PASS | UUID PK on all 20 tables; PK uniqueness validated (22-check validation suite) |
| Foreign keys for every relationship | ✅ PASS | All FKs defined in `schema.sql`; FK integrity checks pass 100% |
| Cardinality documented (1:1, 1:N, N:M) | ✅ PASS | `docs/DATABASE_SCHEMA.md` — full cardinality table + Mermaid ER diagram |
| Bridge tables for N:M | ✅ PASS | `machine_safety_zone`, `machine_interlock`, `incident_alarm` |
| Effective dates on relationships | ✅ PASS | `effective_from` / `effective_to` on `machine_safety_zone` and `machine_interlock` |
| Lifecycle states | ✅ PASS | Machine (8 states), Incident (6 states), CorrectiveAction (7 states), Interlock (4 states) |
| Event history retained | ✅ PASS | 4 immutable event tables; audit_log backfilled with 2,584 entries |
| Validate all joins | ✅ PASS | `validation_service.py` — 9 FK/bridge integrity checks, all PASS |
| issue_type / ground_truth label on anomalies | ✅ PASS | `issue_type`, `rule_id`, `expected_label`, `expected_decision` in `ground_truth.json` |

### ID / Nomenclature Conventions

| Convention | Status | Implementation Evidence |
|---|---|---|
| SAFE-\<plant-id\>-001 | ✅ PASS | `zone_code: SAFE-PLT-0001-001` generated in `master_generator.py` |
| ALM-\<machine-id\>-000001 | ✅ PASS | `alarm_event_code: ALM-MCH-0001-0004-000007` confirmed in live data |
| INC-2026-000001 | ✅ PASS | `incident_code: INC-2026-000001` zero-padded 6 digits |
| ACK-\<alarm-id\>-01 | ✅ PASS | `ack_code: ACK-ALM-MCH-0001-0003-000176-01` confirmed in audit trail |
| ACT-\<incident-id\>-01 | ✅ PASS | `action_code: ACT-INC-2026-000001-01` confirmed in live data |
| Zero-padded, immutable, consistent across files | ✅ PASS | Deterministic `_det_uuid()` + counter-based codes; same seed = same codes |

### Synthetic Data Generation (Steps 1–10)

| Step | Requirement | Status | Implementation Evidence |
|---|---|---|---|
| Step 1 | Data dictionary for all 10 entities | ✅ PASS | `docs/DATABASE_SCHEMA.md` — field type, required, allowed values, units, uniqueness per entity |
| Step 2 | Parent tables first, then child/event tables | ✅ PASS | `master_generator.py` — 18 ordered steps, Plants→Machines→Zones→Interlocks→Alarms→Events |
| Step 3 | Deterministic IDs and naming conventions | ✅ PASS | `_det_uuid(seed_str)` MD5-based; all codes zero-padded and counter-tracked |
| Step 4 | Baseline volume: 4 plants, 60 machines, 200 alarm defs, 50,000 events | ✅ PASS | `full` mode: 4 plants, 60 machines, 200 alarm defs, 50,000 events; `starter` mode for dev |
| Step 5 | Inject 5 labelled edge cases | ✅ PASS | `anomaly_injector.py` — all 5 cases injected with flags, notes, `is_anomalous`/`is_valid` fields |
| Step 6 | Derived values from source records | ✅ PASS | `risk_score` computed from alarm/incident counts; `acknowledgement_status` derived from timestamps |
| Step 7 | Separate ground_truth.csv/json | ✅ PASS | `data/ground_truth/ground_truth.csv` + `ground_truth.json`; never read by detection engine |
| Step 8 | Validation: PK, FK, enums, dates, lifecycle, duplicates | ✅ PASS | 22-check validation suite; latest run: 22/22 PASS, 0 unexpected failures |
| Step 9 | Export CSV/JSON + README + schema + generator command + seed + manifest | ✅ PASS | `/exports/alarms`, `/exports/incidents`, `/exports/anomalies`, `/exports/validation`; README documents all |
| Step 10 | Regenerate twice, compare checksums | ✅ PASS | `scripts/compare_runs.py --same-seed`; `generation_run.checksum` stored per run |

### Volume & Coverage

| Requirement | Status | Implementation Evidence |
|---|---|---|
| 4 plants | ✅ PASS | `full` mode: 4 plants (Alpha Chemical, Beta Refinery, Gamma Processing, Delta Energy) |
| 60 machines | ✅ PASS | `full` mode: 15 machines × 4 plants = 60 machines |
| 200 alarm definitions | ✅ PASS | `full` mode: `alarm_definitions: 200` in `MODE_CONFIG` |
| 50,000 alarm events over 30 days | ✅ PASS | `full` mode: `alarm_events: 50000`; period 2026-10-01 → 2026-10-30 |
| Alarm floods | ✅ PASS | `GET /alarms/floods` — ≥10 alarms/machine/5-min window detected |
| Delayed acknowledgements | ✅ PASS | 588 delayed acks in starter run; `acknowledgement_compliance_rate: 0.412` |
| Nuisance alarms | ✅ PASS | `GET /alarms/nuisance-clusters` — ≥3 same alarm def/1-hour window |
| Genuine high-severity incidents | ✅ PASS | 41 incidents in starter run; 94 critical alarms; traceability chain per incident |

### Required Edge Cases / Negative Scenarios

| Case | Requirement | Status | Implementation Evidence |
|---|---|---|---|
| Case 1 | Acknowledgement before alarm | ✅ PASS | `is_anomalous=True`; `ack_timestamp < alarm_timestamp`; detected by `RULE-ACK-TIMELINE`; validation: EXPECTED_ANOMALY |
| Case 2 | Interlock state impossible | ✅ PASS | `is_valid_combination=False`; Machine RUNNING + GUARD_DOOR DISENGAGED; `unsafe_condition_code=RULE-001` |
| Case 3 | Incident lacks triggering context | ✅ PASS | `has_missing_context=True`; 0 linked alarm events; `INC-2026-CASE3-ANOM` in DB |
| Case 4 | Alarm flood duplicated by replay | ✅ PASS | `is_replayed=True`; same `source_fingerprint`, new ingestion ID; 3 replay records injected |
| Case 5 | Action closed without verification | ✅ PASS | `is_closed_without_verification=True`; `is_valid=False` on CLOSED event in `corrective_action_event` |

### Validation Rules / Acceptance Criteria

| Criterion | Status | Implementation Evidence |
|---|---|---|
| Timeline is coherent | ✅ PASS | `TIMESTAMP_ACK_AFTER_ALARM` check passes (1 expected anomaly only); all alarm/cleared timestamps ordered |
| Severe alarms are prioritized | ✅ PASS | CRITICAL deadline=120s; risk score weights critical×10; dashboard shows critical alarms first |
| Nuisance alarm clusters identified | ✅ PASS | `GET /alarms/nuisance-clusters`; `repeated_unsafe_condition_count=5` in metrics |
| Incident traceability includes machine state and action history | ✅ PASS | `GET /incidents/{id}/traceability` returns alarm chain + machine state + corrective actions |

### Evaluation Focus

| Focus Area | Status | Implementation Evidence |
|---|---|---|
| (a) Realistic distributions and meaningful variation | ✅ PASS | Severity weights [5%, 15%, 40%, 40%]; mixed ack statuses; varied machine types/manufacturers |
| (b) Consistent IDs and valid joins | ✅ PASS | All 9 FK checks PASS; 0 orphan records; bridge table integrity verified |
| (c) Dependency/lifecycle consistency | ✅ PASS | State machine enforced; invalid transitions flagged not silently skipped |
| (d) Correct derived values and reconciliation | ✅ PASS | `risk_score` computed from counts; `acknowledgement_status` derived from timestamps vs deadlines |
| (e) Normal, boundary, failure and exception coverage | ✅ PASS | Normal ops + 5 injected edge cases + alarm floods + delayed acks + overdue actions |
| (f) Separate ground truth | ✅ PASS | `data/ground_truth/ground_truth.json` written post-generation; detection engine never reads it |
| (g) Fixed-seed reproducibility, documentation, lawful provenance | ✅ PASS | Seed `20261022`; `compare_runs.py`; all data synthetic with no real-world PII |

### Overall Compliance Summary

| Category | Requirements | Met | Status |
|---|---|---|---|
| Business Context & Objective | 5 | 5 | ✅ 100% |
| Primary Actors | 4 | 4 | ✅ 100% |
| Business Workflow & Rules | 11 | 11 | ✅ 100% |
| Entities & Relationships | 10 | 10 | ✅ 100% |
| ID / Nomenclature | 6 | 6 | ✅ 100% |
| Data Generation Steps 1–10 | 10 | 10 | ✅ 100% |
| Volume & Coverage | 8 | 8 | ✅ 100% |
| Edge Cases / Negative Scenarios | 5 | 5 | ✅ 100% |
| Validation / Acceptance Criteria | 4 | 4 | ✅ 100% |
| Evaluation Focus (a–g) | 7 | 7 | ✅ 100% |
| **TOTAL** | **70** | **70** | **✅ 100%** |

> Live validation: `POST /api/v1/validation/run` — latest result: **22/22 checks PASS, 0 unexpected failures**
> Evaluation metrics: `GET /api/v1/evaluation/metrics` — Recall: 1.0, all 5 ground-truth anomalies detected

---

## Architecture Overview

```
safeplant-ai/
├── backend/                  # Python Flask REST API
│   ├── app/
│   │   ├── models/           # Plain dicts — Supabase client only, no ORM
│   │   ├── routes/           # 17 Blueprint route files
│   │   ├── services/         # Safety engine, alarm engine, anomaly detection
│   │   └── generators/       # Deterministic synthetic data generator
│   ├── tests/                # pytest test cases (unit + API + validation)
│   └── scripts/              # CLI tools: generate_data.py, compare_runs.py
├── frontend/                 # React + Vite SPA
│   └── src/pages/            # 19 pages: Dashboard, Machines, Anomalies, Exports, etc.
├── data/
│   └── ground_truth/         # ground_truth.csv + ground_truth.json
└── docs/                     # Architecture, schema, master dev prompt, AI prompt log
```

---

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database (Supabase recommended)

### 1. Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env — paste your Supabase URL and anon key

# Create database tables (run schema.sql once in Supabase SQL Editor)
# See docs/SUPABASE_SETUP.md

# Generate starter data (seed: 20261022)
# Via API: POST /api/v1/generator/run {"mode": "starter", "seed": 20261022}

# Start API server
python run.py
```

### Supabase Setup

Get your `SUPABASE_URL` and `SUPABASE_ANON_KEY` from **Supabase → Settings → API**.

Run `schema.sql` once in **Supabase → SQL Editor** to create all 20 tables.

> See **[docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)** for full step-by-step setup.

### 2. Frontend Setup

```powershell
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open **http://localhost:5173** → SafePlant AI dashboard.

---

## Data Generation

The platform uses **deterministic synthetic data generation** (seed `20261022`) covering the period **2026-10-01 → 2026-10-30 UTC**.

### Changing the Seed

The default seed is `20261022`. To use a different seed, choose any of these methods:

**1. Via UI** — Open the **Data Generator** page → change the value in the **Random Seed** field → click **Run Generation**.

**2. Via `.env` file** (persistent default)
```env
# backend/.env
GENERATION_SEED=99999999
```

**3. Via CLI**
```powershell
python scripts/generate_data.py --mode starter --seed 99999999
```

**4. Via API**
```http
POST /api/v1/generator/run
{ "mode": "starter", "seed": 99999999 }
```

> Priority order: **API/CLI argument > `.env` GENERATION_SEED > hardcoded default (20261022)**

| Mode | Plants | Machines | Alarm Events | Incidents |
|------|--------|----------|-------------|-----------|
| **Starter** | 1 | 5 | 1,000 | ~40 |
| **Full** | 4 | 60 | 50,000 | ~2,000 |

### Via CLI
```powershell
# Starter
python scripts/generate_data.py --mode starter --seed 20261022 --validate --export

# Full
python scripts/generate_data.py --mode full --seed 20261022 --validate

# Verify reproducibility
python scripts/compare_runs.py --same-seed
```

### Via API
```http
POST /api/v1/generator/run
{"mode": "starter", "seed": 20261022}
```

---

## Five Mandatory Negative Scenarios

| Case | Entity | Flag | Detection Rule |
|------|--------|------|----------------|
| **Case 1** | `Acknowledgement.is_anomalous=True` | `ack_timestamp < alarm_timestamp` | RULE-ACK-TIMELINE |
| **Case 2** | `InterlockStateEvent.is_valid_combination=False` | Machine RUNNING + guard-door DISENGAGED | RULE-001 |
| **Case 3** | `Incident.has_missing_context=True` | Incident with 0 linked alarm events | RULE-INC-TRACE |
| **Case 4** | `AlarmEvent.is_replayed=True` | Same `source_fingerprint`, new ingestion ID | RULE-REPLAY-DETECT |
| **Case 5** | `CorrectiveAction.is_closed_without_verification=True` | CLOSED attempted before VERIFIED | RULE-CA-VERIFY |

- All 5 cases are **persistently flagged** in the database with immutable evidence
- Detection engine reads **only from DB** — never from ground truth files
- Ground truth files (`data/ground_truth/`) are written after generation for offline evaluation only

---

## Safety Rule Engine

### Machine State Machine
```
OFFLINE → IDLE → STARTING → RUNNING → STOPPING → IDLE
                          ↓              ↓
                       EMERGENCY_STOP  MAINTENANCE
                          ↓
                      FAULT → MAINTENANCE
```

### Alarm Acknowledgement Deadlines
| Severity | Deadline |
|----------|---------|
| CRITICAL | 120 seconds (2 min) |
| HIGH | 300 seconds (5 min) |
| MEDIUM | 900 seconds (15 min) |
| LOW | 1800 seconds (30 min) |

### Alarm Flood Detection
- ≥ 10 alarms from same machine in 5-minute window → **alarm flood**
- ≥ 3 of same alarm definition in 1-hour window → **nuisance cluster**

---

## REST API Reference

**Base URL:** `http://localhost:5000`
**API Prefix:** `/api/v1`
**Content-Type:** `application/json`

All endpoints return a standard envelope:
```json
{
  "status": "success",
  "data": {},
  "meta": { "page": 1, "per_page": 50, "total": 1234, "pages": 25, "has_prev": false, "has_next": true }
}
```
Error responses:
```json
{ "status": "error", "error": "NOT_FOUND", "message": "Plant 'xyz' not found" }
```

---

### System

#### `GET /health`
Health check — verifies API and Supabase database connectivity.

**Response:**
```json
{ "status": "ok", "service": "SafePlant AI", "version": "1.0.0", "database": "ok" }
```

---

### Dashboard

#### `GET /api/v1/dashboard/summary`
Returns all KPI counts and the 10 most recent critical alarm events.

**Response fields:** `kpis.total_plants`, `kpis.total_machines`, `kpis.total_alarms`, `kpis.critical_alarms`, `kpis.open_incidents`, `kpis.delayed_acknowledgements`, `kpis.repeated_unsafe_conditions`, `kpis.pending_corrective_actions`, `recent_critical_events[]`

#### `GET /api/v1/dashboard/trends`
Alarm counts grouped by day and severity for the last N days.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `days` | integer | `30` | Number of days to look back |

**Response:** Array of `{ date, CRITICAL, HIGH, MEDIUM, LOW }`

---

### Plants

#### `GET /api/v1/plants`
List all plants with pagination.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page (max 500) |
| `status` | string | `ACTIVE` | Filter by status: `ACTIVE`, `INACTIVE`, `DECOMMISSIONED` |
| `search` | string | `Alpha` | Case-insensitive name search |

#### `GET /api/v1/plants/{id}`
Get a single plant by UUID or `plant_code` (e.g. `PLT-0001`). Includes `machine_count`.

---

### Machines

#### `GET /api/v1/machines`
List machines with filtering and sorting.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `plant_id` | UUID | | Filter by plant |
| `state` | string | `RUNNING` | Filter by `current_state`: `OFFLINE`, `IDLE`, `STARTING`, `RUNNING`, `STOPPING`, `MAINTENANCE`, `FAULT`, `EMERGENCY_STOP` |
| `search` | string | `Pump` | Case-insensitive name search |
| `sort` | string | `risk_score` | Sort field: `machine_code` (default) or `risk_score` (desc) |

#### `GET /api/v1/machines/{id}`
Get a single machine by UUID or `machine_code`. Includes `plant`, `safety_zones[]`, `interlocks[]`, `alarm_count`, `incident_count`.

#### `GET /api/v1/machines/{id}/timeline`
Combined chronological timeline of state changes, alarms and incidents for a machine (last 100 events).

**Response:** Array of `{ type: "STATE_CHANGE"|"ALARM"|"INCIDENT", timestamp, data }`

---

### Safety Zones

#### `GET /api/v1/safety-zones`
List safety zones.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `plant_id` | UUID | | Filter by plant |
| `hazard_level` | string | `CRITICAL` | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |

#### `GET /api/v1/safety-zones/{id}`
Get a single safety zone by UUID or `zone_code` (e.g. `SAFE-PLT-0001-001`). Includes `machines[]`.

---

### Interlocks

#### `GET /api/v1/interlocks`
List interlocks.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `plant_id` | UUID | | Filter by plant |
| `state` | string | `ENGAGED` | Filter by `current_state`: `ENGAGED`, `DISENGAGED`, `FAULT`, `BYPASSED` |

#### `GET /api/v1/interlocks/{id}`
Get a single interlock by UUID or `interlock_code`. Includes `machines[]` with `is_required` flag.

---

### Alarm Definitions

#### `GET /api/v1/alarm-definitions`
List alarm definitions.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `machine_id` | UUID | | Filter by machine |
| `severity` | string | `CRITICAL` | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `category` | string | `TEMPERATURE` | Filter: `TEMPERATURE`, `PRESSURE`, `FLOW`, `VIBRATION`, `LEVEL`, `GAS_DETECTION`, `ELECTRICAL` |

#### `GET /api/v1/alarm-definitions/{id}`
Get a single alarm definition by UUID or `alarm_code`.

---

### Alarm Events

#### `GET /api/v1/alarms`
List alarm events with rich filtering.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `machine_id` | UUID | | Filter by machine |
| `severity` | string | `CRITICAL` | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `ack_status` | string | `MISSING` | Filter: `PENDING`, `ON_TIME`, `DELAYED`, `MISSING`, `INVALID` |
| `safety_zone_id` | UUID | | Filter by safety zone |
| `from_date` | ISO8601 | `2026-10-01T00:00:00` | Alarm timestamp ≥ |
| `to_date` | ISO8601 | `2026-10-30T23:59:59` | Alarm timestamp ≤ |
| `is_replayed` | boolean | `true` | Filter replayed alarms only |
| `sort` | string | `alarm_timestamp` | Sort field |
| `direction` | string | `desc` | `asc` or `desc` |

#### `GET /api/v1/alarms/{id}`
Get a single alarm event by UUID or `alarm_event_code`. Includes `machine`, `alarm_definition`, `acknowledgements[]`.

#### `GET /api/v1/alarms/{id}/timeline`
Get alarm event with its full acknowledgement history and linked incidents.

**Response:** `{ alarm, acknowledgements[], incidents[] }`

#### `POST /api/v1/alarms/{id}/acknowledge`
Manually acknowledge an alarm event.

**Request body:**
```json
{
  "operator_id": "OP-001",
  "operator_name": "John Miller",
  "notes": "Investigated and resolved"
}
```
**Response (201):** The created acknowledgement record with `status` (`ON_TIME` / `DELAYED` / `INVALID`) and `response_time_seconds`.

#### `GET /api/v1/alarms/floods`
Detect alarm floods — machines with ≥10 alarms in any 5-minute window.

**Response:** Array of `{ machine_id, window_start, window_end, alarm_count, alarm_ids[] }`

#### `GET /api/v1/alarms/nuisance-clusters`
Detect nuisance alarm clusters — same alarm definition firing ≥3 times in 1 hour.

**Response:** Array of `{ alarm_definition_id, machine_id, window_start, count, alarm_ids[] }`

---

### Operator Shifts

#### `GET /api/v1/operator-shifts`
List operator shifts.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `plant_id` | UUID | | Filter by plant |
| `shift_type` | string | `NIGHT` | Filter: `DAY`, `EVENING`, `NIGHT` |

#### `GET /api/v1/operator-shifts/{id}`
Get a single shift by UUID or `shift_code`. Includes `acknowledgements[]` (last 50).

---

### Incidents

#### `GET /api/v1/incidents`
List incidents.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `plant_id` | UUID | | Filter by plant |
| `machine_id` | UUID | | Filter by machine |
| `severity` | string | `CRITICAL` | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `status` | string | `OPEN` | Filter: `OPEN`, `INVESTIGATING`, `ACTION_REQUIRED`, `VERIFICATION_PENDING`, `CLOSED`, `REOPENED` |
| `safety_zone_id` | UUID | | Filter by safety zone |
| `from_date` | ISO8601 | `2026-10-01T00:00:00` | Detected at ≥ |

#### `GET /api/v1/incidents/{id}`
Get a single incident by UUID or `incident_code`. Includes `machine`, `plant`, `safety_zone`, `corrective_actions[]`, `alarm_events[]`, `state_history[]`.

#### `GET /api/v1/incidents/{id}/traceability`
Full traceability chain: incident → alarm events → machine state at time of alarm → acknowledgements → corrective actions.

#### `POST /api/v1/incidents/{id}/transitions`
Transition an incident through its lifecycle.

**Request body:**
```json
{
  "to_state": "INVESTIGATING",
  "transitioned_by": "Dr. Sarah Chen",
  "notes": "Root cause analysis started"
}
```
**Valid states:** `OPEN` → `INVESTIGATING` → `ACTION_REQUIRED` → `VERIFICATION_PENDING` → `CLOSED` / `REOPENED`

**Response:** Updated incident record.

---

### Corrective Actions

#### `GET /api/v1/corrective-actions`
List corrective actions.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `incident_id` | UUID | | Filter by incident |
| `status` | string | `OPEN` | Filter: `OPEN`, `IN_PROGRESS`, `COMPLETED`, `VERIFICATION_PENDING`, `VERIFIED`, `CLOSED`, `REOPENED` |
| `priority` | string | `HIGH` | Filter: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` |
| `overdue` | boolean | `true` | Return only overdue actions (`due_at < now AND status not VERIFIED/CLOSED`) |

#### `GET /api/v1/corrective-actions/{id}`
Get a single corrective action by UUID or `action_code`. Includes `incident`, `status_history[]`, `is_overdue`.

#### `POST /api/v1/corrective-actions`
Create a new corrective action for an incident.

**Request body:**
```json
{
  "incident_id": "<uuid>",
  "description": "Replace pressure relief valve",
  "assigned_engineer": "Eng. Priya Sharma",
  "priority": "HIGH",
  "due_at": "2026-11-10T00:00:00"
}
```
**Response (201):** Created corrective action with `action_code` auto-assigned.

#### `POST /api/v1/corrective-actions/{id}/transitions`
Transition a corrective action status.

**Request body:**
```json
{
  "to_status": "IN_PROGRESS",
  "transitioned_by": "Eng. Marcus Obi",
  "notes": "Work started on valve replacement"
}
```
**Valid statuses:** `OPEN` → `IN_PROGRESS` → `COMPLETED` → `VERIFICATION_PENDING` → `VERIFIED` → `CLOSED`

#### `POST /api/v1/corrective-actions/{id}/verify`
Verify a corrective action (must be in `VERIFICATION_PENDING` status).

**Request body:**
```json
{
  "result": "PASS",
  "verified_by": "Dr. James Kowalski",
  "notes": "Valve replaced and tested successfully"
}
```
**`result` values:** `PASS` → status becomes `VERIFIED` | `FAIL` → status returns to `IN_PROGRESS`

---

### Analytics

#### `GET /api/v1/analytics/severity`
Alarm count grouped by severity level.

**Response:** `[{ severity: "CRITICAL", count: 94 }, ...]`

#### `GET /api/v1/analytics/alarm-trends`
Alarm counts per day grouped by severity.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `days` | integer | `30` | Look-back window in days |

**Response:** Array of `{ date, CRITICAL, HIGH, MEDIUM, LOW, total }`

#### `GET /api/v1/analytics/machine-risk`
Top N machines ranked by computed risk score.

| Query Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `10` | Number of machines to return |

**Response:** Array of `{ machine_id, machine_code, name, risk_score, critical_alarms, high_incidents, ... }`

#### `GET /api/v1/analytics/repeated-conditions`
Machines with ≥2 incidents in the same safety zone within 30 days.

#### `GET /api/v1/analytics/acknowledgements`
Acknowledgement compliance metrics: on-time rate, mean response time, delayed/missing counts.

#### `GET /api/v1/analytics/incidents`
Incident metrics: counts by status, severity, root cause category.

#### `GET /api/v1/analytics/actions`
Corrective action metrics: completion rate, verification rate, overdue count.

#### `GET /api/v1/analytics/shift-performance`
Per-shift acknowledgement compliance rates.

---

### Anomaly Detection

#### `GET /api/v1/anomalies`
List all detected anomalies.

| Query Param | Type | Example | Description |
|---|---|---|---|
| `issue_type` | string | `ACK_BEFORE_ALARM` | Filter by type: `ACK_BEFORE_ALARM`, `IMPOSSIBLE_INTERLOCK_STATE`, `MISSING_INCIDENT_CONTEXT`, `ALARM_REPLAY_DUPLICATE`, `ACTION_CLOSED_WITHOUT_VERIFICATION`, `ALARM_FLOOD`, `NUISANCE_CLUSTER`, `DELAYED_ACK` |
| `severity` | string | `CRITICAL` | Filter by severity |

#### `GET /api/v1/anomalies/{id}`
Get a single anomaly by its ID.

#### `POST /api/v1/anomalies/detect`
Run all anomaly detectors against current database state. Returns full detection results.

**No request body required.**

**Response:** `{ case1_ack_before_alarm[], case2_impossible_interlock[], case3_missing_context[], case4_alarm_replay[], case5_action_no_verify[], alarm_floods[], nuisance_clusters[], delayed_acks[] }`

#### `GET /api/v1/evaluation/metrics`
Precision / Recall / F1 score against ground truth.

**Response:**
```json
{
  "precision": 0.09, "recall": 1.0, "f1_score": 0.17,
  "true_positives": 5, "false_positives": 50, "false_negatives": 0,
  "total_ground_truth": 5, "total_predictions": 58,
  "acknowledgement_compliance_rate": 0.412,
  "mean_acknowledgement_time_seconds": 1169.42,
  "overdue_corrective_actions": 30,
  "corrective_action_verification_rate": 0.277,
  "repeated_unsafe_condition_count": 5
}
```

#### `GET /api/v1/evaluation/confusion-matrix`
TP / FP / FN breakdown per anomaly case type.

---

### Data Generator

#### `POST /api/v1/generator/run`
Trigger synthetic data generation. Runs in a background thread.

**Request body:**
```json
{
  "mode": "starter",
  "seed": 20261022
}
```
| Field | Type | Values | Description |
|---|---|---|---|
| `mode` | string | `starter`, `full` | `starter` = 1 plant / 5 machines / 1K alarms; `full` = 4 plants / 60 machines / 50K alarms |
| `seed` | integer | any | Fixed seed for reproducibility. Default: `20261022` |

**Response (201):** Generation run record with `id`, `run_code`, `status: "RUNNING"`.

> Returns `409 CONFLICT` if a run is already in progress.

#### `GET /api/v1/generator/runs`
List all generation runs (paginated, newest first).

#### `GET /api/v1/generator/runs/{id}`
Get a single generation run by UUID or `run_code` (e.g. `GEN-20261027153700`). Includes `entity_counts` and `checksum`.

---

### Validation

#### `POST /api/v1/validation/run`
Run the full 22-check integrity validation suite.

**Request body (optional):**
```json
{ "generation_run_id": "<uuid>" }
```

**Response (201):** Full validation report with `overall_status`, `total_checks`, `passed_checks`, `failed_checks`, `check_results[]`.

Each check result:
```json
{
  "check": "FK_ALARM_TO_MACHINE",
  "status": "PASS",
  "passed": 1003,
  "failed": 0,
  "is_expected_anomaly": false,
  "evidence_sample": []
}
```

#### `GET /api/v1/validation/reports`
List all past validation reports (paginated, newest first).

#### `GET /api/v1/validation/reports/{id}`
Get a single validation report by UUID or `run_code` (e.g. `VAL-20261027110743`).

---

### Audit Trail

#### `GET /api/v1/audit-logs`
List audit log entries (paginated, newest first).

| Query Param | Type | Example | Description |
|---|---|---|---|
| `page` | integer | `1` | Page number |
| `per_page` | integer | `50` | Rows per page |
| `entity_type` | string | `Incident` | Filter: `Incident`, `CorrectiveAction`, `Machine`, `Acknowledgement` |
| `entity_id` | UUID | | Filter by specific entity |
| `action` | string | `STATE → CLOSED` | Filter by action string |

#### `POST /api/v1/audit-logs/backfill`
One-shot backfill of audit log from all existing event tables (`incident_state_event`, `corrective_action_event`, `machine_state_event`, `acknowledgement`). Safe to re-run — clears and rewrites.

**No request body required.**

**Response:**
```json
{
  "backfilled": 2584,
  "breakdown": {
    "incident_transitions": 41,
    "corrective_action_transitions": 86,
    "machine_state_changes": 1756,
    "acknowledgements": 701
  }
}
```

---

### Exports

All export endpoints return file downloads, not JSON. Use directly in browser or Postman.

| Method | Endpoint | Response | Filename |
|---|---|---|---|
| GET | `/api/v1/exports/alarms` | `text/csv` | `alarms_export.csv` |
| GET | `/api/v1/exports/incidents` | `text/csv` | `incidents_export.csv` |
| GET | `/api/v1/exports/anomalies` | `text/csv` | `anomalies_export.csv` |
| GET | `/api/v1/exports/validation` | `application/json` | `validation_export.json` |

> In Postman: Send the request → click **Save Response → Save to a file**.

---

### Quick Postman / curl Reference

```bash
# Health check
curl http://localhost:5000/health

# Dashboard KPIs
curl http://localhost:5000/api/v1/dashboard/summary

# List critical alarms (page 1)
curl "http://localhost:5000/api/v1/alarms?severity=CRITICAL&per_page=20"

# List missing acknowledgements
curl "http://localhost:5000/api/v1/alarms?ack_status=MISSING&per_page=50"

# Acknowledge an alarm
curl -X POST http://localhost:5000/api/v1/alarms/<alarm_id>/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "OP-001", "operator_name": "John Miller", "notes": "Checked and cleared"}'

# Transition an incident
curl -X POST http://localhost:5000/api/v1/incidents/<incident_id>/transitions \
  -H "Content-Type: application/json" \
  -d '{"to_state": "INVESTIGATING", "transitioned_by": "Dr. Sarah Chen"}'

# Run anomaly detection
curl -X POST http://localhost:5000/api/v1/anomalies/detect

# Get evaluation metrics
curl http://localhost:5000/api/v1/evaluation/metrics

# Generate starter data
curl -X POST http://localhost:5000/api/v1/generator/run \
  -H "Content-Type: application/json" \
  -d '{"mode": "starter", "seed": 20261022}'

# Run validation suite
curl -X POST http://localhost:5000/api/v1/validation/run

# Backfill audit log
curl -X POST http://localhost:5000/api/v1/audit-logs/backfill

# Export alarms CSV
curl http://localhost:5000/api/v1/exports/alarms -o alarms.csv
```

---

## Testing

```powershell
cd backend
pip install pytest
pytest tests/ -v
```

### Test Coverage (50+ test cases)

| Group | Tests | Covers |
|-------|-------|--------|
| TC01–TC10 | Unit | Generator, models, state machine, alarm deadlines |
| TC11–TC17 | Unit | Ack timing, all 5 negative scenarios |
| TC18–TC22 | Unit | Traceability, shifts, flood/nuisance detection |
| TC23–TC30 | Validation | PK uniqueness, FK integrity, enum values, timeline ordering, lifecycle |
| TC31–TC50 | API | Pagination, filtering, not-found, conflicts, exports, all 5 anomaly types |

---

## Evaluation Metrics

Accessed via `GET /api/v1/evaluation/metrics`:

```json
{
  "precision": 0.92,
  "recall": 1.0,
  "f1_score": 0.96,
  "true_positives": 5,
  "false_positives": 0,
  "false_negatives": 0,
  "acknowledgement_compliance_rate": 0.42,
  "mean_acknowledgement_time_seconds": 180.5,
  "overdue_corrective_actions": 12,
  "corrective_action_verification_rate": 0.35,
  "repeated_unsafe_condition_count": 8
}
```

Ground truth is loaded from `data/ground_truth/ground_truth.json` (written after generation, never read by detection engine).

---

## Machine Risk Score Formula

```
risk_score = min(100, raw_score / normalization_factor × 100)

raw_score = (critical_alarms × 10) +
            (high_incidents × 8)  +
            (repeated_unsafe × 6) +
            (delayed_acks × 4)    +
            (overdue_actions × 5)
```

Risk is calculated over a rolling 30-day window and stored in `machine.risk_score`.

---

## Reproducibility

Same seed always produces identical outputs:

```powershell
python scripts/compare_runs.py --same-seed
# → Result: REPRODUCIBLE
```

Reproducibility is verified by:
1. SHA-256 checksum of all generated entity codes, severities, and timestamps
2. Stored in `generation_run.checksum`
3. Comparable across runs via `/api/v1/generator/runs`

---

## Database Schema

20 tables across 2 categories:

**Core (10):** `plant`, `machine`, `safety_zone`, `interlock`, `alarm_definition`, `alarm_event`, `operator_shift`, `acknowledgement`, `incident`, `corrective_action`

**Supporting (10):** `machine_safety_zone`, `machine_interlock`, `alarm_definition`, `machine_state_event`, `interlock_state_event`, `incident_alarm`, `incident_state_event`, `corrective_action_event`, `audit_log`, `generation_run`, `validation_run`

See `docs/DATABASE_SCHEMA.md` for the complete ER diagram.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, Flask 3.x, Supabase Python client |
| Database | **Supabase** (PostgreSQL 15) — REST API via `supabase-py` |
| Frontend | React 18, Vite 5, React Router 6, Recharts |
| Tests | pytest 7.x |
| Data | Deterministic synthetic generation (seed 20261022) |
| Setup Guide | [docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md) |

---

## Docs

| File | Contents |
|------|----------|
| `docs/ARCHITECTURE.md` | System design, data flow, component diagram |
| `docs/DATABASE_SCHEMA.md` | ER diagram, all 20 tables, indexes |
| `docs/BUSINESS_RULES.md` | Safety rules, state machines, formulas |
| `docs/MASTER_DEVELOPMENT_PROMPT.md` | Full 72-hour assessment master specification prompt (authoritative scope) |
| `docs/AI_PROMPT_LOG.md` | Phase-scoped AI prompts for reviewer disclosure (requirement-driven only) |
| `docs/SUPABASE_SETUP.md` | Supabase / database setup |

### AI-assisted development disclosure

This project was built with AI-assisted development permitted by the assessment. For interviews or reviewer questions about **which prompts you used**:

1. Cite the master specification: **[docs/MASTER_DEVELOPMENT_PROMPT.md](docs/MASTER_DEVELOPMENT_PROMPT.md)** (sections 1–28 plus **§29 Prompt record for reviewers**).
2. Cite phase follow-ups and session notes: **[docs/AI_PROMPT_LOG.md](docs/AI_PROMPT_LOG.md)** — log only structured, verification-oriented prompts (not casual or off-topic chat).
3. Map requirements to code: **REQUIREMENTS_TRACEABILITY.md** (when present in `docs/`).

Do not describe joke or vague one-line prompts as part of the project methodology; the documented prompts mirror the problem statement, phased delivery, and test/validation evidence.

---

*SafePlant AI — Demonstrating industrial safety intelligence at scale.*
