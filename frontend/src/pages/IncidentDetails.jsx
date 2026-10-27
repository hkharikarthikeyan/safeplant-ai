import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, GitBranch } from 'lucide-react';
import {
  PageHeader, SeverityBadge, StatusBadge, LoadingSpinner, ErrorState,
  formatTimestamp, useApiData,
} from '../components/common';
import { getIncident, getIncidentTraceability, transitionIncident } from '../api';

const TRANSITIONS = {
  OPEN: ['INVESTIGATING'],
  INVESTIGATING: ['ACTION_REQUIRED', 'REOPENED'],
  ACTION_REQUIRED: ['VERIFICATION_PENDING'],
  VERIFICATION_PENDING: ['CLOSED', 'REOPENED'],
  CLOSED: ['REOPENED'],
  REOPENED: ['INVESTIGATING'],
};

export default function IncidentDetails() {
  const { id } = useParams();
  const { data: incident, loading, error } = useApiData(() => getIncident(id), [id]);
  const { data: traceability } = useApiData(() => getIncidentTraceability(id), [id]);
  const [transitioning, setTransitioning] = useState(false);
  const [transResult, setTransResult] = useState(null);

  const handleTransition = async (toState) => {
    setTransitioning(true);
    try {
      await transitionIncident(id, { to_state: toState, transitioned_by: 'Web Operator', notes: `Manual: ${toState}` });
      setTransResult({ success: true, msg: `Transitioned to ${toState}` });
      window.location.reload();
    } catch (e) {
      setTransResult({ success: false, msg: e.message });
    } finally {
      setTransitioning(false);
    }
  };

  if (loading) return <div className="page-container"><LoadingSpinner /></div>;
  if (error) return <div className="page-container"><ErrorState message={error} /></div>;
  if (!incident) return null;

  const allowedTransitions = TRANSITIONS[incident.status] || [];

  return (
    <div className="page-container">
      <div style={{ marginBottom: 16 }}>
        <Link to="/incidents" className="btn btn-secondary btn-sm"><ArrowLeft size={13} /> Back to Incidents</Link>
      </div>

      <PageHeader
        title={<span className="mono">{incident.incident_code}</span>}
        subtitle={incident.description}
        actions={allowedTransitions.map(ts => (
          <button key={ts} className="btn btn-primary btn-sm" onClick={() => handleTransition(ts)} disabled={transitioning}>
            → {ts}
          </button>
        ))}
      />

      {transResult && (
        <div className="error-state" style={{
          background: transResult.success ? 'var(--color-success-bg)' : 'var(--color-critical-bg)',
          borderColor: transResult.success ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)',
          color: transResult.success ? 'var(--color-success)' : 'var(--color-critical)',
        }}>
          {transResult.success ? `✓ ${transResult.msg}` : `✗ ${transResult.msg}`}
        </div>
      )}

      {/* Anomaly flags */}
      {incident.has_missing_context && (
        <div className="error-state">
          ⚠ <strong>CASE 3 ANOMALY:</strong> This incident was created without required triggering alarm context.
          Traceability is incomplete.
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">Incident Details</span></div>
          <table style={{ width: '100%', fontSize: 13 }}>
            <tbody>
              {[
                ['Severity', <SeverityBadge severity={incident.severity} />],
                ['Status', <StatusBadge status={incident.status} />],
                ['Root Cause', incident.root_cause_category],
                ['Engineer', incident.assigned_engineer],
                ['Detected', formatTimestamp(incident.detected_at)],
                ['Closed', formatTimestamp(incident.closed_at)],
                ['Missing Context', incident.has_missing_context ? <span className="badge badge-critical">YES</span> : 'No'],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td style={{ color: 'var(--color-text-muted)', padding: '5px 0', width: 140 }}>{k}</td>
                  <td style={{ padding: '5px 0' }}>{v ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title"><GitBranch size={14} /> State History</span></div>
          {(incident.state_history || []).map((se, i) => (
            <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid var(--color-border-subtle)', fontSize: 12 }}>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                {se.from_state && <StatusBadge status={se.from_state} />}
                {se.from_state && <span style={{ color: 'var(--color-text-muted)' }}>→</span>}
                <StatusBadge status={se.to_state} />
                {!se.is_valid && <span className="badge badge-critical">INVALID</span>}
              </div>
              <div style={{ color: 'var(--color-text-muted)', marginTop: 2 }}>
                {se.transitioned_by} · {formatTimestamp(se.transitioned_at)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Traceability Chain */}
      {traceability && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <span className="card-title">Traceability Chain</span>
            <span className={`badge ${traceability.traceability_complete ? 'badge-success' : 'badge-critical'}`}>
              {traceability.traceability_complete ? 'COMPLETE' : 'INCOMPLETE'}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
            Triggering Alarms: {traceability.triggering_alarms?.length || 0}
          </div>
          {(traceability.triggering_alarms || []).map(alarm => (
            <div key={alarm.id} style={{ padding: '6px 10px', background: 'var(--color-bg-secondary)', borderRadius: 6, marginBottom: 6, fontSize: 12 }}>
              <span className="mono">{alarm.alarm_event_code}</span>
              {' · '}<SeverityBadge severity={alarm.severity} />
              {' · '}{formatTimestamp(alarm.alarm_timestamp)}
            </div>
          ))}
        </div>
      )}

      {/* Corrective Actions */}
      <div className="card">
        <div className="card-header"><span className="card-title">Corrective Actions</span></div>
        {(incident.corrective_actions || []).length === 0
          ? <div style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>No corrective actions</div>
          : incident.corrective_actions.map(ca => (
            <div key={ca.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--color-border-subtle)' }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                <span className="mono" style={{ fontSize: 11 }}>{ca.action_code}</span>
                <StatusBadge status={ca.status} />
                {ca.is_closed_without_verification && <span className="badge badge-critical">CASE 5 — NO VERIFY</span>}
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>{ca.description}</div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>
                Due: {formatTimestamp(ca.due_at)} · Engineer: {ca.assigned_engineer}
              </div>
            </div>
          ))
        }
      </div>
    </div>
  );
}
