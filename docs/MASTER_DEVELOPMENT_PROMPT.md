# Master Development Prompt

**SafePlant AI — Industrial Safety Monitoring & Incident Intelligence System**  
**72-Hour Full-Stack Coding Assessment**

> **AI-assisted development disclosure:** Reviewers often ask which prompts were used. This file is the **authoritative master specification prompt** for the project. Phase-scoped follow-ups and a session log live in [AI_PROMPT_LOG.md](./AI_PROMPT_LOG.md). Document only requirement-driven, verification-oriented prompts for assessment—not informal or unrelated chat.

---

## 1. YOUR ROLE

Act as a team consisting of:

- Senior Full-Stack Software Architect
- React Frontend Engineer
- Python Flask Backend Engineer
- PostgreSQL Database Architect
- Industrial Safety Domain Analyst
- Data Engineer and Synthetic Data Specialist
- QA Automation Engineer
- UI/UX Designer
- Technical Documentation Engineer

Your responsibility is to design, implement, test, and document a complete, working, interview-ready application.

**Project Name:** SafePlant AI — Industrial Safety Monitoring & Incident Intelligence System

**Project Objective:** Build an end-to-end industrial safety intelligence platform that analyzes machine safety events, machine states, interlocks, alarm acknowledgements, operator shifts, incidents, and corrective actions to identify repeated unsafe conditions.

The application must provide operational visibility, explainable safety decisions, traceable incident histories, anomaly detection, and measurable evaluation results.

This is a functional coding assessment, not a UI-only prototype.

- Do not generate mock dashboard numbers or disconnected frontend demonstrations.
- All displayed information must come from the Flask API, backed by generated and persisted database records.

---

## 2. MANDATORY TECHNOLOGY STACK

**Frontend:** React with Vite, JavaScript (JSX), Tailwind CSS, React Router, Axios, Recharts, Lucide React icons, TanStack Table where appropriate.

**Backend:** Python 3.11+, Flask, Flask-Migrate, Flask-CORS,request validation, Python logging, Pandas and NumPy for generation and analysis, Pytest for automated testing.

**Database:** PostgreSQL (preferred- supabase), proper indexes, foreign keys, and constraints.

**Development:** Git, GitHub, Python virtual environment, `.env` configuration, Docker Compose where practical.

Do not introduce paid services, unnecessary cloud dependencies, external AI APIs, or complex microservices. Use a modular monolithic architecture appropriate. The application must work locally without external API keys.

---

## 3. NON-NEGOTIABLE REQUIREMENTS

Implement every requirement in the supplied problem statement. Specifically:

- Create all 10 required business entities.
- Define primary keys, foreign keys, relationships, and cardinalities.
- Generate parent/master data before dependent records.
- Generate 4 plants, 60 machines, 200 alarm definitions, and exactly 50,000 baseline alarm events over 30 days.
- Use the fixed seed **20261022**.
- Provide configurable starter and full generation modes.
- Preserve deterministic IDs and exact cross-file references.
- Implement machine states and state transitions, safety zones and interlock evaluation, severity-based alarm rules, operator shifts and acknowledgement deadlines, incident creation from documented unsafe conditions, corrective action workflows, immutable event and transition history.
- Inject all five mandatory negative scenarios; generate separate ground-truth files.
- Implement comprehensive data integrity validation; export CSV, JSON, and SQL seed files; produce a source manifest and validation report.
- Demonstrate reproducibility using two independent generations.
- Implement a complete responsive React frontend and working Flask REST APIs.
- Include automated tests and a professional README; show measurable detection results and traceability.
- Do not silently ignore any failed requirement.
- Create **REQUIREMENTS_TRACEABILITY.md** mapping every requirement to implementation, API, automated test, and verification evidence.

---

## 4. PROJECT FOLDER STRUCTURE

Create the following structure:

```text
safeplant-ai/
  frontend/          src/api, components, pages (Dashboard, Plants, Machines, … AuditTrail), hooks, App.jsx, vite.config.js
  backend/           app/models, routes, schemas, services, generators, migrations, tests, scripts, run.py
  data/              starter/, full/, ground_truth/, exports/, manifests/
  docs/              ARCHITECTURE.md, DATABASE_SCHEMA.md, … REQUIREMENTS_TRACEABILITY.md, DEMO_GUIDE.md
  docker-compose.yml
  README.md
  .gitignore
```

Required React pages include: Dashboard, Plants, Machines, MachineDetails, SafetyZones, Interlocks, AlarmDefinitions, Alarms, AlarmDetails, OperatorShifts, Incidents, IncidentDetails, CorrectiveActions, Analytics, Anomalies, DataGenerator, Validation, AuditTrail.

Required backend services include: `safety_engine.py`, `alarm_engine.py`, `incident_engine.py`, `anomaly_engine.py`, `analytics_service.py`, `validation_service.py`, `export_service.py`, and generators (`master_generator.py`, `event_generator.py`, `anomaly_injector.py`, `ground_truth_generator.py`, `reproducibility.py`).

Scripts: `generate_data.py`, `validate_data.py`, `export_data.py`, `compare_runs.py`.

You may add necessary files and folders, but do not remove required functionality.

---

## 5. DATABASE DESIGN

Implement mandatory entities: **Plant**, **Machine**, **SafetyZone**, **Interlock**, **AlarmDefinition**, **AlarmEvent**, **OperatorShift**, **Acknowledgement**, **Incident**, **CorrectiveAction**, plus supporting entities (machine/interlock state events, bridge tables, audit/generation/validation runs, etc.).

For every entity define PKs, FKs, fields, types, constraints, lifecycle, and cardinalities. Use bridge tables for N:M. No cascading deletes that destroy historical safety evidence; use soft deactivation on master records. UTC internally; readable timestamps in UI. Index common query paths. Document assumptions in **ASSUMPTIONS.md**.

---

## 6. DETERMINISTIC ID RULES

- Safety reference: `SAFE-<plant-id>-001`
- Alarm event: `ALM-<machine-id>-000001`
- Incident: `INC-2026-000001`
- Acknowledgement: `ACK-<alarm-id>-01`
- Corrective action: `ACT-<incident-id>-01`

Use immutable, zero-padded identifiers from deterministic counters and stable ordering. Preserve full referenced IDs without truncation. All exports must preserve the same IDs.

---

## 7. SYNTHETIC DATA GENERATOR

Deterministic, parameterized generator with fixed seed **20261022**, 30 consecutive days in 2026 (document exact start/end).

**Full:** 4 plants, 60 machines, 200 alarm definitions, exactly 50,000 baseline alarm events, plus zones, interlocks, shifts, states, acks, incidents, corrective actions.

**Starter:** 1 plant, 5 machines, 20 alarm definitions, 1,000 baseline alarm events.

Same generator implementation for both modes. Example CLI:

```bash
python scripts/generate_data.py --mode starter --seed 20261022
python scripts/generate_data.py --mode full --seed 20261022
```

Generate in order: plants → machines → zones → interlocks → associations → alarm definitions → shifts → state events → alarm events → acks → incidents → corrective actions → lifecycle → labelled anomalies → ground truth → derived analytics. Derive alarms and incidents from machine conditions, not independent random labels.

---

## 8. SAFETY RULE ENGINE

Configurable, deterministic engine with documented machine states (OFFLINE, IDLE, STARTING, RUNNING, STOPPING, MAINTENANCE, FAULT, EMERGENCY_STOP) and valid transitions; interlock states (ENGAGED, DISENGAGED, FAULT, BYPASSED). Rules for unsafe combinations (e.g. RUNNING with guard disengaged), repeated high-severity alarms, delayed/missing acks, etc. Separate evaluation from HTTP/UI. Each detection exposes rule ID, description, machine, zone, source events, timestamp, severity, expected decision, explanation. This is a synthetic analytics prototype—not a certified safety controller.

---

## 9. ALARM SEVERITY AND ACKNOWLEDGEMENT RULES

Default deadlines: CRITICAL 2 min, HIGH 5 min, MEDIUM 15 min, LOW 30 min (demonstration rules). Statuses: PENDING, ON_TIME, DELAYED, MISSING, INVALID—computed from timestamps, not assigned arbitrarily. Preserve all acknowledgement attempts; flag ack-before-alarm as INVALID without silently correcting timestamps.

---

## 10. INCIDENT MANAGEMENT

Incidents from safety rules with full traceability (alarms, state events, timeline). States: OPEN → INVESTIGATING → ACTION_REQUIRED → VERIFICATION_PENDING → CLOSED (REOPENED allowed). Reject invalid transitions; persist immutable transition events. Detail API returns complete traceability chain.

---

## 11. CORRECTIVE ACTION WORKFLOW

Full lifecycle with verification required before valid CLOSED. Preserve invalid closure attempts in history. Overdue detection. Statuses: OPEN, IN_PROGRESS, COMPLETED, VERIFICATION_PENDING, VERIFIED, CLOSED, REOPENED.

---

## 12. FIVE MANDATORY NEGATIVE SCENARIOS

1. **Acknowledgement before alarm** — INVALID ack, temporal flag, ground truth.
2. **Impossible interlock state** — rule violation detected, history preserved.
3. **Incident without triggering context** — traceability failure, no fabricated alarm.
4. **Alarm flood duplicated by replay** — duplicate/replay fingerprint, distinct ingestion IDs.
5. **Action closed without verification** — lifecycle violation, state unchanged, anomaly labelled.

Each with stable anomaly IDs, issue_type, entity IDs, rule_id, expected decision, evidence, severity, ground-truth label.

---

## 13. GROUND-TRUTH DATA

`data/ground_truth/ground_truth.csv` and `.json` with documented columns. Detection logic must **never** read ground truth; use only for offline evaluation. Separate predictions file; match on stable anomaly identities.

---

## 14. ANOMALY DETECTION AND EVALUATION

Rule-based detection for all listed categories. Metrics: TP, FP, FN, TN, precision, recall, F1, coverage, per-type recall, FPR, compliance rates, mean ack time, closure times, verification rate, repeated unsafe counts. Define evaluation unit explicitly; handle zero denominators; **never hardcode 100% metrics**. **EVALUATION_REPORT.md** with measured outcomes and limitations.

---

## 15. FLASK REST API DESIGN

Implement versioned REST endpoints under **`/api/v1`**.

**System:** `GET /health`, `GET /api/v1/dashboard/summary`, `GET /api/v1/dashboard/trends`

**Master data:** plants, machines (`/:id`, `/:id/timeline`), safety-zones, interlocks, alarm-definitions, operator-shifts

**Alarms:** list, detail, timeline, `POST …/acknowledge`, floods, nuisance-clusters

**Incidents:** list, detail, traceability, `POST …/transitions`

**Corrective actions:** list, detail, create, transitions, verify

**Analytics:** severity, alarm-trends, machine-risk, repeated-conditions, acknowledgements, incidents, actions, shift-performance

**Anomalies:** list, detail, `POST /anomalies/detect`; **Evaluation:** metrics, confusion-matrix

**Generator:** `POST /generator/run`, runs list/detail

**Validation:** run, reports list/detail

**Exports:** alarms, incidents, anomalies, validation

**Audit:** `GET /api/v1/audit-logs`

Filters: plant, machine, severity, status, date range, safety zone, shift, anomaly type. Pagination for large collections. Status codes: 200, 201, 400, 404, 409, 422, 500 with standardized error bodies. Protect generation/evaluation from accidental overlapping runs. Document with sample requests and responses.

---

## 16. FRONTEND DESIGN REQUIREMENTS

Industrial SaaS UI: dark sidebar, light content, teal/blue accents, severity colors, React Router sidebar navigation to all entity pages. Dashboard KPIs and charts from live APIs only. Machine/alarm/incident/corrective/anomaly/analytics/validation/generator/audit pages with filters, pagination, timelines, and explainable anomaly detail.

---

## 17. RISK SCORING

Explainable 0–100 machine risk from stored events (critical alarms, incidents, repeated unsafe, delayed acks, overdue actions, interlock violations). Document formula in **BUSINESS_RULES.md**; not a certified industrial assessment.

---

## 18. VALIDATION ENGINE

Automated checks: PK/FK, enums, timestamps, lifecycles, ack deadlines, replay duplicates, missing incident context, invalid interlocks, reconciliation, ID formats, ground-truth separation, reproducibility. Distinguish expected injected anomalies from unexpected failures. **VALIDATION_REPORT.md** with actual output.

---

## 19. AUTOMATED TESTING

Pytest (backend) and Vitest/React Testing Library (frontend): unit, integration, API, and generator tests.

**Mandatory scenarios TC01–TC50** including: plant/machine FKs and zones; exactly 200 alarm defs and 50,000 events in full mode; deterministic seed; valid/invalid machine transitions; ack on-time/delayed/before-alarm; all five negative scenarios; traceability; flood and nuisance detection; repeated unsafe conditions; PK/FK/enum/timeline/lifecycle checks; ground-truth separation; precision/recall/F1; API pagination, invalid input, not-found, conflicts; CSV/JSON/SQL export; same-seed checksum; different-seed variation; React dashboard integration; rollback; replay idempotency; shift boundaries; bridge integrity; verification history; large-dataset performance; generator re-run safety; all five injected types in ground truth and detectable.

For each test document: Test ID, purpose, input, expected result, actual result, pass/fail. Do not mark unexecuted tests as passed. Fix failures and rerun.

---

## 20. DATA EXPORTS

CSV/JSON/SQL per entity; ground truth; predictions; validation and evaluation JSON; **source_manifest.json** with generator version, seed, counts, checksums, config. Synthetic data only; metadata must not break deterministic checksums.

---

## 21. REPRODUCIBILITY

Same seed → identical outputs (counts, sorted content, IDs, SHA-256, ground truth). Different seed → valid but varied data. Document exact commands and results.

---

## 22. README REQUIREMENTS

Professional root **README.md** with installation, generation modes, run commands, API overview, safety/anomaly explanation, tests, validation, evaluation, reproducibility, exports, demo instructions, Windows PowerShell and cross-platform commands, known limitations—**no invented test results or screenshots**.

---

## 23. ADDITIONAL DOCUMENTATION

**ARCHITECTURE.md**, **DATABASE_SCHEMA.md**, **DATA_DICTIONARY.md**, **BUSINESS_RULES.md**, **API_DOCUMENTATION.md**, **TEST_CASES.md**, **REQUIREMENTS_TRACEABILITY.md**, **VALIDATION_REPORT.md**, **EVALUATION_REPORT.md**, **DEMO_GUIDE.md**, **ASSUMPTIONS.md**.

---

## 24. SECURITY AND RELIABILITY

Input validation, ORM parameterization, CORS, env secrets, safe errors, transactions, audit log, pagination, indexing, safe exports, request limits. No client modification of immutable safety history. Simple documented actor/RBAC if time permits—do not misrepresent as production auth.

---

## 25. DEVELOPMENT PHASES

Implement in order: **Phase 1** Architecture & requirements → **Phase 2** Backend foundation → **Phase 3** Synthetic data generator → **Phase 4** Safety & detection → **Phase 5** REST APIs → **Phase 6** React frontend → **Phase 7** Testing & optimization → **Phase 8** Documentation & submission.

---

## 26. IMPORTANT CODING INSTRUCTIONS

AI-assisted development is expected.

- Generate **complete working code**, not pseudocode.
- No placeholders: TODO, mock API, dummy data, “coming soon”.
- Per phase: list files created/modified, full source, dependencies, exact commands, verification steps, tests, doc updates.
- Create/modify actual project files when workspace access is available.
- Work phase by phase; do not claim execution without evidence.
- **Maintain [AI_PROMPT_LOG.md](./AI_PROMPT_LOG.md)** with phase-scoped prompts used for implementation (for reviewer transparency).

---

## 27. FINAL ACCEPTANCE GATE

Ready for submission only when: frontend and backend start; DB initializes; all entities and relationships; starter/full generation; five negative scenarios detectable; ground truth separate from detection; traceable timelines; dashboard uses API data; exports and validation/evaluation/reproducibility complete; mandatory tests executed; README/docs complete; local demo possible.

Produce a final completion report with completed/incomplete requirements, entity counts, test/validation/evaluation/reproducibility results, limitations, and start commands—**do not report success without evidence**.

---

## 28. START DEVELOPMENT NOW

Begin with **PHASE 1**: architecture, Mermaid ER diagram, data dictionary, business rules, requirements traceability matrix, implementation plan—then proceed phase by phase.

Prioritize correctness, deterministic generation, safety-rule traceability, and test coverage over unnecessary visual complexity.

---

## 29. PROMPT RECORD FOR REVIEWERS (ASSESSMENT DISCLOSURE)

When asked **“What prompts did you use?”** in an interview or assessment, answer with this documented set:

| What to share | Where |
|---------------|--------|
| Master specification (full scope, stack, volumes, APIs, tests, acceptance gate) | This file: **MASTER_DEVELOPMENT_PROMPT.md** |
| Phase follow-ups and dated session notes | **AI_PROMPT_LOG.md** |
| Requirement-to-code mapping | **REQUIREMENTS_TRACEABILITY.md** |

**Share prompts that:**

- Reference explicit requirements (10 entities, seed 20261022, 50k events, five negative cases, TC01–TC50).
- Are organized by **development phase** with verification steps (pytest, validation run, `compare_runs.py`).
- Instruct the assistant not to fabricate metrics, tests, or deployment outcomes.

**Do not share or describe as “project prompts”:**

- Vague one-line requests without acceptance criteria.
- Joke, meme, or unrelated chat unrelated to SafePlant AI.
- Prompts that ask to skip backend integration or hardcode dashboard numbers.

**Interview framing (example):**  
*“I used one master specification prompt that mirrors the assessment problem statement, then phase-specific prompts for the generator, safety engines, APIs, and React UI. I logged those in `docs/AI_PROMPT_LOG.md` and verified each phase with automated tests and validation scripts—not mock data.”*

---

*End of master development prompt.*
