# AI Prompt Log — SafePlant AI

Use this file when reviewers or interviewers ask **which prompts you used** for AI-assisted development. List only **project-relevant, requirement-driven** prompts. Do not include casual chat, unrelated experiments, or humorous one-liners.

## Canonical prompts

| ID | When used | Prompt role | Location / summary |
|----|-----------|-------------|-------------------|
| P0 | Project start | **Master development specification** — full stack, entities, generator, APIs, tests, docs, acceptance gate | [MASTER_DEVELOPMENT_PROMPT.md](./MASTER_DEVELOPMENT_PROMPT.md) |
| P1 | Phase 1 | Architecture, ER diagram, data dictionary, business rules, requirements traceability | Follow-up: *"Begin PHASE 1 per master prompt; produce ARCHITECTURE, DATABASE_SCHEMA, BUSINESS_RULES, REQUIREMENTS_TRACEABILITY."* |
| P2 | Phase 2 | Flask foundation, models, migrations, error handling | Follow-up: *"Implement PHASE 2 backend foundation per master prompt; include pytest for models and app factory."* |
| P3 | Phase 3 | Deterministic generator (seed 20261022), starter/full modes, ground truth | Follow-up: *"Implement PHASE 3 synthetic data generator with ordered steps and five injected negative scenarios."* |
| P4 | Phase 4 | Safety, alarm, incident, anomaly engines; validation and evaluation | Follow-up: *"Implement PHASE 4 engines; detection must not read ground-truth files."* |
| P5 | Phase 5 | REST API `/api/v1` per endpoint list | Follow-up: *"Implement PHASE 5 routes with pagination, filters, and standardized errors."* |
| P6 | Phase 6 | React dashboard and entity pages wired to Flask APIs | Follow-up: *"Implement PHASE 6 frontend; no hardcoded KPIs or mock APIs."* |
| P7 | Phase 7 | Test matrix TC01–TC50, reproducibility, performance | Follow-up: *"Execute mandatory tests; fix failures; document actual results in TEST_CASES.md."* |
| P8 | Phase 8 | README, demo guide, validation/evaluation reports | Follow-up: *"Complete PHASE 8 documentation; do not invent test or metric outcomes."* |

## Session log (fill in as you work)

Add one row per meaningful AI session. Keep descriptions factual.

| Date | Phase | What you asked the assistant to do | Verification you ran |
|------|-------|--------------------------------------|----------------------|
| _example_ | 3 | Generate full dataset with `--mode full --seed 20261022` | `pytest tests/generator/` ; row counts vs spec |
| | | | |

## What assessors expect

- Prompts tied to **explicit requirements** (entities, volumes, five negative cases, APIs, tests).
- **Phased** delivery matching the master prompt, not a single vague “build the app.”
- **Verification commands** (pytest, validation run, reproducibility compare) after each phase.
- Honest disclosure if a requirement is incomplete (see final acceptance gate in master prompt).

## What not to cite in an interview

- Generic prompts with no acceptance criteria (“make it look cool”, “fix everything”).
- Prompts that ask to **fake** test results, screenshots, or deployment success.
- Off-topic or joke prompts unrelated to SafePlant AI.

The **single source of truth** for scope remains [MASTER_DEVELOPMENT_PROMPT.md](./MASTER_DEVELOPMENT_PROMPT.md).
