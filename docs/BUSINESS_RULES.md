# Business Rules — SafePlant AI

## 1. Machine State Machine

### Valid States
| State | Description |
|-------|-------------|
| OFFLINE | Machine powered down |
| IDLE | Powered but not running |
| STARTING | Start-up sequence active |
| RUNNING | Normal operation |
| STOPPING | Shutdown sequence active |
| MAINTENANCE | Under scheduled maintenance |
| FAULT | Non-critical fault detected |
| EMERGENCY_STOP | Emergency stop activated |

### Valid Transitions

```
OFFLINE      → IDLE
IDLE         → STARTING, MAINTENANCE, OFFLINE
STARTING     → RUNNING, FAULT, EMERGENCY_STOP
RUNNING      → STOPPING, FAULT, EMERGENCY_STOP, MAINTENANCE
STOPPING     → IDLE, FAULT
MAINTENANCE  → IDLE, OFFLINE
FAULT        → MAINTENANCE, IDLE, EMERGENCY_STOP
EMERGENCY_STOP → MAINTENANCE, OFFLINE
```

Any other transition is INVALID and must be recorded as such (flag: `is_valid_transition = False`).

---

## 2. Interlock States

| State | Description |
|-------|-------------|
| ENGAGED | Interlock active and protecting |
| DISENGAGED | Interlock not active |
| FAULT | Interlock hardware fault |
| BYPASSED | Manually overridden |

---

## 3. Safety Rules (Rule Engine)

### RULE-001: Running Machine with Guard Door Disengaged
- **Condition**: Machine state = RUNNING AND associated guard-door interlock state = DISENGAGED
- **Severity**: CRITICAL
- **Action**: Create incident, flag unsafe condition

### RULE-002: Running Machine with Emergency Stop Engaged
- **Condition**: Machine state = RUNNING AND emergency-stop interlock state = ENGAGED
- **Severity**: CRITICAL
- **Action**: Create incident

### RULE-003: Running Machine with Required Safety Interlock Bypassed
- **Condition**: Machine state = RUNNING AND MachineInterlock.is_required = True AND interlock state = BYPASSED
- **Severity**: HIGH
- **Action**: Create incident, flag bypass event

### RULE-004: Critical Temperature Alarm During Active Operation
- **Condition**: AlarmDefinition.category = 'TEMPERATURE' AND severity = CRITICAL AND machine state IN (RUNNING, STARTING)
- **Severity**: CRITICAL
- **Action**: Trigger incident creation

### RULE-005: Repeated High-Severity Alarms Within Window
- **Condition**: ≥ 3 HIGH or CRITICAL alarms from same machine within 15-minute window
- **Severity**: HIGH
- **Action**: Flag as nuisance cluster or alarm flood

### RULE-006: Critical Alarm with Missing or Delayed Acknowledgement
- **Condition**: CRITICAL alarm not acknowledged within 2 minutes (120 seconds)
- **Severity**: HIGH
- **Action**: Flag delayed acknowledgement, contribute to risk score

### RULE-007: Machine Restarted Before Required Safety Verification
- **Condition**: Machine transitions FAULT/EMERGENCY_STOP → STARTING without a VERIFIED corrective action
- **Severity**: HIGH
- **Action**: Flag unsafe restart

### RULE-008: Repeated Incidents Involving Same Machine and Safety Zone
- **Condition**: ≥ 2 incidents on same machine_id + safety_zone_id within 30 days
- **Severity**: MEDIUM
- **Action**: Flag repeated unsafe condition

### RULE-009: Alarm Flood Detection
- **Condition**: ≥ 10 alarms from any machine within a 5-minute window
- **Severity**: MEDIUM
- **Action**: Create alarm flood record

### RULE-010: Invalid Interlock State Combination
- **Condition**: Machine state = RUNNING AND any required interlock in state FAULT
- **Severity**: CRITICAL
- **Action**: Detect impossible combination

---

## 4. Acknowledgement Rules

| Severity | Deadline (seconds) | Deadline (readable) |
|----------|--------------------|---------------------|
| CRITICAL | 120 | 2 minutes |
| HIGH | 300 | 5 minutes |
| MEDIUM | 900 | 15 minutes |
| LOW | 1800 | 30 minutes |

These are **project-defined demonstration rules**, not official industrial standards.

### Acknowledgement Status Calculation
1. If no acknowledgement record exists AND deadline has passed → `MISSING`
2. If no acknowledgement record exists AND deadline has not passed → `PENDING`
3. If ack_timestamp < alarm_timestamp → `INVALID` (anomalous)
4. If (ack_timestamp - alarm_timestamp) ≤ deadline → `ON_TIME`
5. If (ack_timestamp - alarm_timestamp) > deadline → `DELAYED`

### First Valid Acknowledgement
- Multiple acknowledgement attempts are preserved
- The first record where `validation_result = VALID` and `ack_timestamp >= alarm_timestamp` is used for compliance calculation
- All attempts remain in the audit trail

---

## 5. Incident Lifecycle

```
OPEN → INVESTIGATING → ACTION_REQUIRED → VERIFICATION_PENDING → CLOSED
                                      ↑                       ↓
                                   REOPENED ←─────────────────┘
```

### Transition Rules
- OPEN → INVESTIGATING: Always allowed
- INVESTIGATING → ACTION_REQUIRED: Requires at least one corrective action created
- ACTION_REQUIRED → VERIFICATION_PENDING: All corrective actions must be COMPLETED
- VERIFICATION_PENDING → CLOSED: All corrective actions must be VERIFIED
- ANY → REOPENED: Allowed if new evidence discovered
- REOPENED → INVESTIGATING: Always allowed

Any other transition is INVALID and must be recorded with `is_valid = False`.

---

## 6. Corrective Action Lifecycle

```
OPEN → IN_PROGRESS → COMPLETED → VERIFICATION_PENDING → VERIFIED → CLOSED
                                                       ↑          ↓
                                                    REOPENED ←────┘
```

### Transition Rules
- COMPLETED without prior verification → status can reach CLOSED only if VERIFIED first
- Attempting CLOSED without VERIFIED is flagged as lifecycle violation
- Invalid closure attempt is preserved in CorrectiveActionEvent with `is_valid = False`

### Overdue Detection
- `due_at < now() AND status NOT IN (VERIFIED, CLOSED)` → overdue

---

## 7. Risk Score Formula

Machine risk score (0–100):

```
risk_score = min(100, (
    (critical_alarm_count * 10) +
    (high_incident_count * 8) +
    (repeated_unsafe_conditions * 6) +
    (delayed_ack_count * 4) +
    (overdue_actions * 5) +
    (interlock_violations * 7)
) / normalization_factor * 100)
```

**Weights** (configurable in `config.py`):
| Factor | Weight |
|--------|--------|
| Critical alarms (last 30 days) | 10 |
| High/critical incidents | 8 |
| Repeated unsafe conditions | 6 |
| Delayed acknowledgements | 4 |
| Overdue corrective actions | 5 |
| Interlock violations | 7 |

**Normalization factor**: Sum of all weights × expected maximum count per factor

This is a **heuristic score for demonstration purposes**, not a certified industrial risk assessment.

---

## 8. Alarm Flood Definition

An **alarm flood** is defined as ≥ 10 alarm events from any single machine within a 5-minute sliding window.

A **nuisance alarm cluster** is defined as ≥ 3 alarms of the same `alarm_definition_id` within a 1-hour window (indicating false/recurring trips).

---

## 9. Repeated Unsafe Condition

A machine is flagged for **repeated unsafe conditions** when:
- ≥ 2 incidents on the same `machine_id` AND `safety_zone_id` within the 30-day generation window
- The triggering rule is the same (same `rule_id`)

---

## 10. ID Format Rules

| Entity | Format | Example |
|--------|--------|---------|
| Plant | PLT-{N:04d} | PLT-0001 |
| Machine | MCH-{plant_seq}-{N:04d} | MCH-0001-0001 |
| SafetyZone | SAFE-{plant_code}-{N:03d} | SAFE-PLT-0001-001 |
| AlarmDefinition | ALMDEF-{machine_code}-{N:03d} | ALMDEF-MCH-0001-0001-001 |
| AlarmEvent | ALM-{machine_code}-{N:06d} | ALM-MCH-0001-0001-000001 |
| Incident | INC-2026-{N:06d} | INC-2026-000001 |
| Acknowledgement | ACK-{alarm_event_code}-{N:02d} | ACK-ALM-MCH-0001-0001-000001-01 |
| CorrectiveAction | ACT-{incident_code}-{N:02d} | ACT-INC-2026-000001-01 |
| OperatorShift | SHIFT-{plant_code}-{N:05d} | SHIFT-PLT-0001-00001 |
| GenerationRun | GEN-{YYYYMMDD}-{N:04d} | GEN-20261022-0001 |
