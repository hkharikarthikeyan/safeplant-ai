import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import {
  PageHeader, SeverityBadge, StatusBadge, LoadingSpinner,
  ErrorState, formatTimestamp, useApiData,
} from '../components/common';
import { getAlarm, acknowledgeAlarm } from '../api';

export default function AlarmDetails() {
  const { id } = useParams();
  const { data: alarm, loading, error } = useApiData(() => getAlarm(id), [id]);
  const [acking, setAcking] = useState(false);
  const [ackResult, setAckResult] = useState(null);

  const handleAck = async () => {
    setAcking(true);
    try {
      const res = await acknowledgeAlarm(id, { operator_id: 'OP-WEB', operator_name: 'Web Operator' });
      setAckResult({ success: true, data: res.data?.data });
    } catch (e) {
      setAckResult({ success: false, message: e.message });
    } finally {
      setAcking(false);
    }
  };

  if (loading) return <div className="page-container"><LoadingSpinner /></div>;
  if (error) return <div className="page-container"><ErrorState message={error} /></div>;
  if (!alarm) return null;

  return (
    <div className="page-container">
      <div style={{ marginBottom: 16 }}>
        <Link to="/alarms" className="btn btn-secondary btn-sm"><ArrowLeft size={13} /> Back to Alarms</Link>
      </div>
      <PageHeader
        title={<span className="mono">{alarm.alarm_event_code}</span>}
        subtitle="Alarm Event Details"
        actions={
          alarm.acknowledgement_status === 'PENDING' && (
            <button className="btn btn-primary btn-sm" onClick={handleAck} disabled={acking}>
              {acking ? 'Acknowledging…' : 'Acknowledge'}
            </button>
          )
        }
      />
      {ackResult && (
        <div className={ackResult.success ? 'error-state' : 'error-state'}
          style={{ background: ackResult.success ? 'var(--color-success-bg)' : 'var(--color-critical-bg)', borderColor: ackResult.success ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)', color: ackResult.success ? 'var(--color-success)' : 'var(--color-critical)' }}>
          {ackResult.success ? `✓ Acknowledged — Status: ${ackResult.data?.status}` : `✗ ${ackResult.message}`}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div className="card">
          <div className="card-header"><span className="card-title">Alarm Details</span></div>
          <table style={{ width: '100%', fontSize: 13 }}>
            <tbody>
              {[
                ['Severity', <SeverityBadge severity={alarm.severity} />],
                ['Status', <StatusBadge status={alarm.status} />],
                ['Ack Status', <StatusBadge status={alarm.acknowledgement_status} />],
                ['Trigger Value', alarm.trigger_value],
                ['Alarm Time', formatTimestamp(alarm.alarm_timestamp)],
                ['Cleared Time', formatTimestamp(alarm.cleared_timestamp)],
                ['Replayed', alarm.is_replayed ? <span className="badge badge-info">YES — CASE 4</span> : 'No'],
                ['Fingerprint', <span className="mono" style={{ fontSize: 10 }}>{alarm.source_fingerprint}</span>],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td style={{ color: 'var(--color-text-muted)', padding: '5px 0', width: 130 }}>{k}</td>
                  <td style={{ padding: '5px 0' }}>{v ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Acknowledgements</span></div>
          {(alarm.acknowledgements || []).length === 0
            ? <div style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>No acknowledgements recorded</div>
            : alarm.acknowledgements.map(ack => (
              <div key={ack.id} style={{ padding: '8px 0', borderBottom: '1px solid var(--color-border-subtle)' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <StatusBadge status={ack.status} />
                  {ack.is_anomalous && <span className="badge badge-critical">ANOMALY</span>}
                </div>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 3 }}>
                  {ack.operator_name} · {formatTimestamp(ack.ack_timestamp)} · Response: {ack.response_time_seconds}s
                </div>
                {ack.notes && <div style={{ fontSize: 11, color: 'var(--color-warning)', marginTop: 2 }}>{ack.notes}</div>}
              </div>
            ))
          }
        </div>
      </div>

      {/* Linked Incidents */}
      {alarm.alarm_definition && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header"><span className="card-title">Alarm Definition</span></div>
          <div style={{ fontSize: 13, display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Name: </span>{alarm.alarm_definition.name}</div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Category: </span>{alarm.alarm_definition.category}</div>
            <div><span style={{ color: 'var(--color-text-muted)' }}>Deadline: </span>{alarm.alarm_definition.ack_deadline_seconds}s</div>
          </div>
        </div>
      )}
    </div>
  );
}
