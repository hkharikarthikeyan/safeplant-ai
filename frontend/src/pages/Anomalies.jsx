import React, { useState } from 'react';
import { Search, RefreshCw, ChevronRight } from 'lucide-react';
import {
  PageHeader, SeverityBadge, StatusBadge, LoadingSpinner, ErrorState,
  EmptyState, useApiData, formatTimestamp,
} from '../components/common';
import { getAnomalies, detectAnomalies, getEvaluationMetrics, getConfusionMatrix } from '../api';

const ISSUE_TYPES = [
  '', 'ACK_BEFORE_ALARM', 'IMPOSSIBLE_INTERLOCK_STATE',
  'MISSING_INCIDENT_CONTEXT', 'ALARM_REPLAY_DUPLICATE',
  'ACTION_CLOSED_WITHOUT_VERIFICATION', 'DELAYED_CRITICAL_ACK',
];

const CASE_MAP = {
  ACK_BEFORE_ALARM: { label: 'Case 1', color: 'var(--color-critical)' },
  IMPOSSIBLE_INTERLOCK_STATE: { label: 'Case 2', color: 'var(--color-critical)' },
  MISSING_INCIDENT_CONTEXT: { label: 'Case 3', color: 'var(--color-high)' },
  ALARM_REPLAY_DUPLICATE: { label: 'Case 4', color: 'var(--color-warning)' },
  ACTION_CLOSED_WITHOUT_VERIFICATION: { label: 'Case 5', color: 'var(--color-high)' },
};

export default function Anomalies() {
  const [issueType, setIssueType] = useState('');
  const [severity, setSeverity] = useState('');
  const [detecting, setDetecting] = useState(false);
  const [detectMsg, setDetectMsg] = useState(null);

  const { data: anomalies, loading, error } = useApiData(
    () => getAnomalies({ ...(issueType && { issue_type: issueType }), ...(severity && { severity }) }),
    [issueType, severity]
  );
  const { data: metrics } = useApiData(getEvaluationMetrics);
  const { data: matrix } = useApiData(getConfusionMatrix);

  const handleDetect = async () => {
    setDetecting(true);
    setDetectMsg(null);
    try {
      const res = await detectAnomalies();
      setDetectMsg({ success: true, msg: `Detection complete — ${res.data?.data?.total_detected} anomalies found` });
    } catch (e) {
      setDetectMsg({ success: false, msg: e.message });
    } finally {
      setDetecting(false);
    }
  };

  const items = Array.isArray(anomalies) ? anomalies : [];

  return (
    <div className="page-container">
      <PageHeader
        title="Anomaly Detection"
        subtitle="5 mandatory negative scenarios + rule-based anomaly detection"
        actions={
          <button className="btn btn-primary" onClick={handleDetect} disabled={detecting}>
            <RefreshCw size={13} /> {detecting ? 'Running…' : 'Run Detection'}
          </button>
        }
      />

      {detectMsg && (
        <div className="error-state" style={{
          background: detectMsg.success ? 'var(--color-success-bg)' : 'var(--color-critical-bg)',
          borderColor: detectMsg.success ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)',
          color: detectMsg.success ? 'var(--color-success)' : 'var(--color-critical)',
          marginBottom: 16,
        }}>
          {detectMsg.msg}
        </div>
      )}

      {/* Evaluation Metrics */}
      {metrics && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header"><span className="card-title">Evaluation Metrics</span></div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {[
              ['Precision', `${(metrics.precision * 100).toFixed(1)}%`],
              ['Recall', `${(metrics.recall * 100).toFixed(1)}%`],
              ['F1 Score', `${(metrics.f1_score * 100).toFixed(1)}%`],
              ['True Positives', metrics.true_positives],
              ['False Positives', metrics.false_positives],
              ['False Negatives', metrics.false_negatives],
              ['Ack Compliance', `${(metrics.acknowledgement_compliance_rate * 100).toFixed(1)}%`],
              ['Overdue Actions', metrics.overdue_corrective_actions],
              ['CA Verify Rate', `${(metrics.corrective_action_verification_rate * 100).toFixed(1)}%`],
              ['Repeated Unsafe', metrics.repeated_unsafe_condition_count],
            ].map(([k, v]) => (
              <div key={k} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px' }}>{k}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--color-teal)', fontFamily: 'JetBrains Mono, monospace' }}>{v}</div>
              </div>
            ))}
          </div>
          {matrix && (
            <div style={{ marginTop: 14, padding: '10px 14px', background: 'var(--color-bg-secondary)', borderRadius: 6, fontSize: 12, color: 'var(--color-text-muted)' }}>
              <strong>Confusion Matrix:</strong> TP={matrix.matrix?.true_positive} · FP={matrix.matrix?.false_positive} · FN={matrix.matrix?.false_negative}
              {' · '}<em>{matrix.note}</em>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="filters-row">
        <select className="form-control" value={issueType} onChange={e => setIssueType(e.target.value)}>
          {ISSUE_TYPES.map(t => <option key={t} value={t}>{t || 'All Issue Types'}</option>)}
        </select>
        <select className="form-control" value={severity} onChange={e => setSeverity(e.target.value)}>
          {['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
        </select>
      </div>

      {loading && <LoadingSpinner text="Detecting anomalies..." />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
            {items.length} anomal{items.length === 1 ? 'y' : 'ies'} found
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {items.length === 0 && <EmptyState message="No anomalies detected. Run detection or generate data first." icon="🔍" />}
            {items.map(anomaly => {
              const caseInfo = CASE_MAP[anomaly.issue_type];
              return (
                <div key={anomaly.anomaly_id} className="card" style={{
                  borderLeft: `3px solid ${caseInfo?.color || 'var(--color-border)'}`,
                  padding: '14px 18px',
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6, flexWrap: 'wrap' }}>
                        <span className="mono" style={{ fontSize: 12, color: 'var(--color-teal)' }}>{anomaly.anomaly_id}</span>
                        {caseInfo && (
                          <span className="badge badge-critical" style={{ background: 'rgba(248,113,113,0.15)' }}>{caseInfo.label}</span>
                        )}
                        <SeverityBadge severity={anomaly.severity} />
                        <span className="badge badge-muted" style={{ fontSize: 10 }}>{anomaly.issue_type?.replace(/_/g, ' ')}</span>
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>
                        {anomaly.description}
                      </div>
                      <div style={{ marginTop: 6, display: 'flex', gap: 12, fontSize: 11, color: 'var(--color-text-muted)' }}>
                        <span>Entity: <span className="mono">{anomaly.entity_id?.slice(0, 16)}…</span></span>
                        <span>Rule: <span className="mono">{anomaly.rule_id}</span></span>
                        <span>Decision: <strong>{anomaly.expected_decision}</strong></span>
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)', whiteSpace: 'nowrap', textAlign: 'right' }}>
                      {formatTimestamp(anomaly.detected_at)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
