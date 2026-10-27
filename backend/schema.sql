-- ============================================================
-- SafePlant AI — Complete Database Schema
-- Run this ONCE in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CORE ENTITY 1: Plant
-- ============================================================
CREATE TABLE IF NOT EXISTS plant (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    plant_code    TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    location      TEXT NOT NULL,
    region        TEXT NOT NULL,
    timezone      TEXT NOT NULL DEFAULT 'UTC',
    status        TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','DECOMMISSIONED')),
    is_active     BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CORE ENTITY 2: Machine
-- ============================================================
CREATE TABLE IF NOT EXISTS machine (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    machine_code    TEXT UNIQUE NOT NULL,
    plant_id        TEXT NOT NULL REFERENCES plant(id),
    name            TEXT NOT NULL,
    machine_type    TEXT NOT NULL,
    model_number    TEXT,
    manufacturer    TEXT,
    current_state   TEXT NOT NULL DEFAULT 'OFFLINE'
                    CHECK (current_state IN ('OFFLINE','IDLE','STARTING','RUNNING','STOPPING','MAINTENANCE','FAULT','EMERGENCY_STOP')),
    risk_score      NUMERIC(5,2) NOT NULL DEFAULT 0.0,
    status          TEXT NOT NULL DEFAULT 'ACTIVE',
    commissioned_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_machine_plant ON machine(plant_id);
CREATE INDEX IF NOT EXISTS idx_machine_state ON machine(current_state);

-- ============================================================
-- CORE ENTITY 3: SafetyZone
-- ============================================================
CREATE TABLE IF NOT EXISTS safety_zone (
    id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    zone_code    TEXT UNIQUE NOT NULL,
    plant_id     TEXT NOT NULL REFERENCES plant(id),
    name         TEXT NOT NULL,
    zone_type    TEXT NOT NULL,
    hazard_level TEXT NOT NULL DEFAULT 'MEDIUM'
                 CHECK (hazard_level IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    description  TEXT,
    is_active    BOOLEAN NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CORE ENTITY 4: Interlock
-- ============================================================
CREATE TABLE IF NOT EXISTS interlock (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    interlock_code      TEXT UNIQUE NOT NULL,
    plant_id            TEXT NOT NULL REFERENCES plant(id),
    name                TEXT NOT NULL,
    interlock_type      TEXT NOT NULL,
    current_state       TEXT NOT NULL DEFAULT 'ENGAGED'
                        CHECK (current_state IN ('ENGAGED','DISENGAGED','FAULT','BYPASSED')),
    description         TEXT,
    is_safety_critical  BOOLEAN NOT NULL DEFAULT true,
    is_active           BOOLEAN NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- BRIDGE: Machine ↔ SafetyZone
-- ============================================================
CREATE TABLE IF NOT EXISTS machine_safety_zone (
    id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    machine_id     TEXT NOT NULL REFERENCES machine(id),
    safety_zone_id TEXT NOT NULL REFERENCES safety_zone(id),
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to   TIMESTAMPTZ,
    UNIQUE (machine_id, safety_zone_id)
);

-- ============================================================
-- BRIDGE: Machine ↔ Interlock
-- ============================================================
CREATE TABLE IF NOT EXISTS machine_interlock (
    id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    machine_id     TEXT NOT NULL REFERENCES machine(id),
    interlock_id   TEXT NOT NULL REFERENCES interlock(id),
    is_required    BOOLEAN NOT NULL DEFAULT true,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to   TIMESTAMPTZ,
    UNIQUE (machine_id, interlock_id)
);

-- ============================================================
-- CORE ENTITY 5: AlarmDefinition
-- ============================================================
CREATE TABLE IF NOT EXISTS alarm_definition (
    id                   TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    alarm_code           TEXT UNIQUE NOT NULL,
    machine_id           TEXT NOT NULL REFERENCES machine(id),
    name                 TEXT NOT NULL,
    description          TEXT,
    severity             TEXT NOT NULL CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    category             TEXT NOT NULL,
    threshold_value      NUMERIC,
    threshold_unit       TEXT,
    ack_deadline_seconds INTEGER NOT NULL,
    is_active            BOOLEAN NOT NULL DEFAULT true,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- CORE ENTITY 6: AlarmEvent
-- ============================================================
CREATE TABLE IF NOT EXISTS alarm_event (
    id                     TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    alarm_event_code       TEXT UNIQUE NOT NULL,
    alarm_definition_id    TEXT NOT NULL REFERENCES alarm_definition(id),
    machine_id             TEXT NOT NULL REFERENCES machine(id),
    safety_zone_id         TEXT REFERENCES safety_zone(id),
    trigger_value          NUMERIC,
    severity               TEXT NOT NULL CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    status                 TEXT NOT NULL DEFAULT 'ACTIVE',
    acknowledgement_status TEXT NOT NULL DEFAULT 'PENDING'
                           CHECK (acknowledgement_status IN ('PENDING','ON_TIME','DELAYED','MISSING','INVALID')),
    alarm_timestamp        TIMESTAMPTZ NOT NULL,
    cleared_timestamp      TIMESTAMPTZ,
    ingested_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_fingerprint     TEXT,
    is_replayed            BOOLEAN NOT NULL DEFAULT false,
    generation_run_id      TEXT
);
CREATE INDEX IF NOT EXISTS idx_alarm_event_machine   ON alarm_event(machine_id);
CREATE INDEX IF NOT EXISTS idx_alarm_event_severity  ON alarm_event(severity);
CREATE INDEX IF NOT EXISTS idx_alarm_event_timestamp ON alarm_event(alarm_timestamp);
CREATE INDEX IF NOT EXISTS idx_alarm_event_ack       ON alarm_event(acknowledgement_status);
CREATE INDEX IF NOT EXISTS idx_alarm_event_fp        ON alarm_event(source_fingerprint);

-- ============================================================
-- CORE ENTITY 7: OperatorShift
-- ============================================================
CREATE TABLE IF NOT EXISTS operator_shift (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    shift_code    TEXT UNIQUE NOT NULL,
    plant_id      TEXT NOT NULL REFERENCES plant(id),
    operator_name TEXT NOT NULL,
    operator_id   TEXT NOT NULL,
    shift_type    TEXT NOT NULL CHECK (shift_type IN ('DAY','EVENING','NIGHT')),
    shift_start   TIMESTAMPTZ NOT NULL,
    shift_end     TIMESTAMPTZ NOT NULL,
    status        TEXT NOT NULL DEFAULT 'COMPLETED',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_shift_plant ON operator_shift(plant_id);
CREATE INDEX IF NOT EXISTS idx_shift_dates ON operator_shift(shift_start, shift_end);

-- ============================================================
-- CORE ENTITY 8: Acknowledgement
-- ============================================================
CREATE TABLE IF NOT EXISTS acknowledgement (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    ack_code            TEXT UNIQUE NOT NULL,
    alarm_event_id      TEXT NOT NULL REFERENCES alarm_event(id),
    operator_shift_id   TEXT REFERENCES operator_shift(id),
    operator_id         TEXT,
    operator_name       TEXT,
    ack_timestamp       TIMESTAMPTZ NOT NULL,
    response_time_seconds INTEGER,
    status              TEXT NOT NULL CHECK (status IN ('PENDING','ON_TIME','DELAYED','MISSING','INVALID')),
    validation_result   TEXT CHECK (validation_result IN ('VALID','INVALID')),
    notes               TEXT,
    is_anomalous        BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ack_alarm ON acknowledgement(alarm_event_id);
CREATE INDEX IF NOT EXISTS idx_ack_shift ON acknowledgement(operator_shift_id);

-- ============================================================
-- CORE ENTITY 9: Incident
-- ============================================================
CREATE TABLE IF NOT EXISTS incident (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    incident_code       TEXT UNIQUE NOT NULL,
    plant_id            TEXT NOT NULL REFERENCES plant(id),
    machine_id          TEXT NOT NULL REFERENCES machine(id),
    safety_zone_id      TEXT REFERENCES safety_zone(id),
    severity            TEXT NOT NULL CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    status              TEXT NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN','INVESTIGATING','ACTION_REQUIRED','VERIFICATION_PENDING','CLOSED','REOPENED')),
    root_cause_category TEXT,
    description         TEXT NOT NULL,
    assigned_engineer   TEXT,
    detected_at         TIMESTAMPTZ NOT NULL,
    closed_at           TIMESTAMPTZ,
    has_missing_context BOOLEAN NOT NULL DEFAULT false,
    generation_run_id   TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_incident_machine   ON incident(machine_id);
CREATE INDEX IF NOT EXISTS idx_incident_status    ON incident(status);
CREATE INDEX IF NOT EXISTS idx_incident_severity  ON incident(severity);
CREATE INDEX IF NOT EXISTS idx_incident_detected  ON incident(detected_at);

-- ============================================================
-- CORE ENTITY 10: CorrectiveAction
-- ============================================================
CREATE TABLE IF NOT EXISTS corrective_action (
    id                              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    action_code                     TEXT UNIQUE NOT NULL,
    incident_id                     TEXT NOT NULL REFERENCES incident(id),
    description                     TEXT NOT NULL,
    assigned_engineer               TEXT,
    priority                        TEXT NOT NULL DEFAULT 'MEDIUM' CHECK (priority IN ('CRITICAL','HIGH','MEDIUM','LOW')),
    status                          TEXT NOT NULL DEFAULT 'OPEN'
                                    CHECK (status IN ('OPEN','IN_PROGRESS','COMPLETED','VERIFICATION_PENDING','VERIFIED','CLOSED','REOPENED')),
    due_at                          TIMESTAMPTZ,
    completed_at                    TIMESTAMPTZ,
    verified_at                     TIMESTAMPTZ,
    verification_result             TEXT CHECK (verification_result IN ('PASS','FAIL')),
    is_closed_without_verification  BOOLEAN NOT NULL DEFAULT false,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SUPPORTING: IncidentAlarm bridge
-- ============================================================
CREATE TABLE IF NOT EXISTS incident_alarm (
    id                TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    incident_id       TEXT NOT NULL REFERENCES incident(id),
    alarm_event_id    TEXT NOT NULL REFERENCES alarm_event(id),
    relationship_type TEXT DEFAULT 'TRIGGER',
    linked_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (incident_id, alarm_event_id)
);

-- ============================================================
-- SUPPORTING: IncidentStateEvent (immutable history)
-- ============================================================
CREATE TABLE IF NOT EXISTS incident_state_event (
    id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    incident_id     TEXT NOT NULL REFERENCES incident(id),
    from_state      TEXT,
    to_state        TEXT NOT NULL,
    transitioned_by TEXT,
    notes           TEXT,
    is_valid        BOOLEAN NOT NULL DEFAULT true,
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SUPPORTING: CorrectiveActionEvent (immutable history)
-- ============================================================
CREATE TABLE IF NOT EXISTS corrective_action_event (
    id                    TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    corrective_action_id  TEXT NOT NULL REFERENCES corrective_action(id),
    from_status           TEXT,
    to_status             TEXT NOT NULL,
    transitioned_by       TEXT,
    notes                 TEXT,
    is_valid              BOOLEAN NOT NULL DEFAULT true,
    transitioned_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- SUPPORTING: MachineStateEvent (immutable history)
-- ============================================================
CREATE TABLE IF NOT EXISTS machine_state_event (
    id                    TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    machine_id            TEXT NOT NULL REFERENCES machine(id),
    from_state            TEXT,
    to_state              TEXT NOT NULL,
    is_valid_transition   BOOLEAN NOT NULL DEFAULT true,
    trigger_reason        TEXT,
    occurred_at           TIMESTAMPTZ NOT NULL,
    generation_run_id     TEXT
);
CREATE INDEX IF NOT EXISTS idx_mse_machine    ON machine_state_event(machine_id);
CREATE INDEX IF NOT EXISTS idx_mse_timestamp  ON machine_state_event(occurred_at);

-- ============================================================
-- SUPPORTING: InterlockStateEvent (immutable history)
-- ============================================================
CREATE TABLE IF NOT EXISTS interlock_state_event (
    id                    TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    interlock_id          TEXT NOT NULL REFERENCES interlock(id),
    machine_id            TEXT NOT NULL REFERENCES machine(id),
    from_state            TEXT,
    to_state              TEXT NOT NULL,
    is_valid_combination  BOOLEAN NOT NULL DEFAULT true,
    unsafe_condition_code TEXT,
    occurred_at           TIMESTAMPTZ NOT NULL,
    generation_run_id     TEXT
);

-- ============================================================
-- SUPPORTING: AuditLog
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    entity_type  TEXT NOT NULL,
    entity_id    TEXT NOT NULL,
    action       TEXT NOT NULL,
    actor        TEXT,
    before_state JSONB,
    after_state  JSONB,
    ip_address   TEXT,
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_time   ON audit_log(occurred_at);

-- ============================================================
-- SUPPORTING: GenerationRun
-- ============================================================
CREATE TABLE IF NOT EXISTS generation_run (
    id            TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    run_code      TEXT UNIQUE NOT NULL,
    mode          TEXT NOT NULL,
    seed          INTEGER NOT NULL,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'RUNNING',
    entity_counts JSONB,
    configuration JSONB,
    checksum      TEXT
);

-- ============================================================
-- SUPPORTING: ValidationRun
-- ============================================================
CREATE TABLE IF NOT EXISTS validation_run (
    id                  TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    run_code            TEXT UNIQUE NOT NULL,
    generation_run_id   TEXT REFERENCES generation_run(id),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ,
    overall_status      TEXT,
    check_results       JSONB,
    total_checks        INTEGER DEFAULT 0,
    passed_checks       INTEGER DEFAULT 0,
    failed_checks       INTEGER DEFAULT 0,
    expected_anomalies  INTEGER DEFAULT 0,
    unexpected_failures INTEGER DEFAULT 0
);

-- ============================================================
-- Row Level Security — allow anon key full access for dev
-- (In production: add proper RLS policies)
-- ============================================================
ALTER TABLE plant                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE machine               ENABLE ROW LEVEL SECURITY;
ALTER TABLE safety_zone           ENABLE ROW LEVEL SECURITY;
ALTER TABLE interlock             ENABLE ROW LEVEL SECURITY;
ALTER TABLE machine_safety_zone   ENABLE ROW LEVEL SECURITY;
ALTER TABLE machine_interlock     ENABLE ROW LEVEL SECURITY;
ALTER TABLE alarm_definition      ENABLE ROW LEVEL SECURITY;
ALTER TABLE alarm_event           ENABLE ROW LEVEL SECURITY;
ALTER TABLE operator_shift        ENABLE ROW LEVEL SECURITY;
ALTER TABLE acknowledgement       ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident              ENABLE ROW LEVEL SECURITY;
ALTER TABLE corrective_action     ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_alarm        ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident_state_event  ENABLE ROW LEVEL SECURITY;
ALTER TABLE corrective_action_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE machine_state_event   ENABLE ROW LEVEL SECURITY;
ALTER TABLE interlock_state_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log             ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_run        ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_run        ENABLE ROW LEVEL SECURITY;

-- Grant anon full access (all operations via API key)
DO $$
DECLARE
    tbl TEXT;
    tables TEXT[] := ARRAY[
        'plant','machine','safety_zone','interlock',
        'machine_safety_zone','machine_interlock',
        'alarm_definition','alarm_event','operator_shift','acknowledgement',
        'incident','corrective_action','incident_alarm','incident_state_event',
        'corrective_action_event','machine_state_event','interlock_state_event',
        'audit_log','generation_run','validation_run'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('CREATE POLICY "anon_all_%s" ON %I FOR ALL TO anon USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;
