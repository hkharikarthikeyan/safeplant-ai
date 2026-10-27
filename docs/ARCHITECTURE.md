# SafePlant AI — System Architecture

## Overview

SafePlant AI is a modular monolithic industrial safety intelligence platform. It provides operational visibility, explainable safety decisions, traceable incident histories, anomaly detection, and measurable evaluation results for industrial plant environments.

---

## Architecture Pattern

**Modular Monolith** — chosen for 72-hour assessment scope:

- Single deployable backend service
- Clear internal module boundaries
- Shared database connection pool
- In-process service communication
- Testable in isolation per module

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  Dashboard | Machines | Alarms | Incidents | Analytics       │
│  React Router | Axios | Recharts | TanStack Table            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST (JSON)
                           │ CORS controlled
┌──────────────────────────▼──────────────────────────────────┐
│               Flask REST API (Python 3.11+)                  │
│  /api/v1/...                                                 │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Routes  │ │ Schemas  │ │Services  │ │  Generators  │   │
│  │          │ │(Marshmallow)│          │ │              │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │            │            │               │            │
│  ┌────▼────────────▼────────────▼───────────────▼────────┐  │
│  │              SQLAlchemy ORM Layer                      │  │
│  └────────────────────────┬───────────────────────────────┘  │
└───────────────────────────┼─────────────────────────────────┘
                            │ psycopg2
┌───────────────────────────▼─────────────────────────────────┐
│              PostgreSQL Database (Supabase)                  │
│  10 core entities + 10 supporting entities                   │
│  Indexes | FK Constraints | Soft Delete                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Normal Operation
1. Frontend → API request with filters/pagination
2. Flask route validates request (Marshmallow)
3. Service layer queries ORM
4. ORM executes parameterized SQL
5. Results serialized → JSON response

### Data Generation Flow
1. CLI / API trigger → `generate_data.py`
2. `master_generator.py` → Plants, Machines, Zones, Interlocks
3. `event_generator.py` → Machine states, Alarms, Shifts
4. `anomaly_injector.py` → 5 negative scenarios
5. `ground_truth_generator.py` → Separate CSV/JSON ground truth
6. All records persisted to PostgreSQL
7. Export service writes CSV/JSON/SQL files

### Anomaly Detection Flow
1. Detection triggered via API or CLI
2. `safety_engine.py` evaluates rules against DB records
3. Predictions written to `predictions.csv`
4. `validation_service.py` compares against ground truth
5. Evaluation metrics computed and stored

---

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `routes/` | HTTP request handling, parameter extraction |
| `schemas/` | Request/response validation and serialization |
| `services/safety_engine.py` | Machine state + interlock rule evaluation |
| `services/alarm_engine.py` | Severity rules, acknowledgement deadlines |
| `services/incident_engine.py` | Incident lifecycle, traceability |
| `services/anomaly_engine.py` | Anomaly detection, evaluation metrics |
| `services/analytics_service.py` | Risk scoring, trend analysis |
| `services/validation_service.py` | Data integrity checks |
| `services/export_service.py` | CSV/JSON/SQL export |
| `generators/master_generator.py` | Deterministic master data |
| `generators/event_generator.py` | Deterministic event streams |
| `generators/anomaly_injector.py` | 5 mandatory negative scenarios |
| `generators/ground_truth_generator.py` | Separate ground truth files |
| `generators/reproducibility.py` | Checksum comparison |

---

## Security Decisions

- ORM prevents SQL injection (parameterized queries)
- CORS restricted to frontend origin
- Secrets in `.env` (never committed)
- Historical safety records are immutable (no DELETE on alarm/incident events)
- Soft delete for master records
- Audit log for all state transitions
- Request body size limit: 1 MB

---

## Performance Decisions

- Server-side pagination (default 50 rows, max 500)
- Database indexes on: machine_id, alarm_id, severity, status, timestamp, shift_id
- Query optimization with select_related (joinedload)
- Export streams for large datasets

---

## Architectural Assumptions

- Single-region PostgreSQL (Supabase free tier sufficient for assessment)
- No caching layer (dataset size manageable in PostgreSQL)
- No message queue (synchronous generation acceptable)
- No authentication (demo mode; documented in ASSUMPTIONS.md)
- UTC timestamps stored; client-side timezone display
