import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Activity, Cpu, ShieldAlert, Zap } from 'lucide-react';
import {
  PageHeader, StatusBadge, SeverityBadge, RiskBar, LoadingSpinner,
  ErrorState, formatTimestamp, useApiData,
} from '../components/common';
import { getMachine, getMachineTimeline } from '../api';

function TimelineItem({ item }) {
  const { type, data, timestamp } = item;
  const dotClass = type === 'ALARM' && data.severity === 'CRITICAL' ? 'critical' :
    type === 'INCIDENT' ? 'warning' : '';
  return (
    <div className="timeline-item">
      <div className={`timeline-dot ${dotClass}`} />
      <div className="timeline-content">
        <div className="timeline-meta">{formatTimestamp(timestamp)} — {type.replace('_', ' ')}</div>
        {type === 'STATE_CHANGE' && (
          <div style={{ fontSize: 13 }}>
            State: <StatusBadge status={data.from_state} /> → <StatusBadge status={data.to_state} />
            {!data.is_valid_transition && (
              <span className="badge badge-critical" style={{ marginLeft: 8 }}>INVALID</span>
            )}
          </div>
        )}
        {type === 'ALARM' && (
          <div style={{ fontSize: 13 }}>
            <span className="mono">{data.alarm_event_code}</span>
            {' · '}<SeverityBadge severity={data.severity} />
            {' · '}Ack: <StatusBadge status={data.acknowledgement_status} />
          </div>
        )}
        {type === 'INCIDENT' && (
          <div style={{ fontSize: 13 }}>
            <span className="mono">{data.incident_code}</span>
            {' · '}<SeverityBadge severity={data.severity} />
            {' · '}<StatusBadge status={data.status} />
          </div>
        )}
      </div>
    </div>
  );
}

export default function MachineDetails() {
  const { id } = useParams();
  const { data: machine, loading: ml, error: me } = useApiData(() => getMachine(id), [id]);
  const { data: timeline, loading: tl } = useApiData(() => getMachineTimeline(id), [id]);

  if (ml) return <div className="page-container"><LoadingSpinner /></div>;
  if (me) return <div className="page-container"><ErrorState message={me} /></div>;
  if (!machine) return null;

  return (
    <div className="page-container">
      <div style={{ marginBottom: 16 }}>
        <Link to="/machines" className="btn btn-secondary btn-sm"><ArrowLeft size={13} /> Back to Machines</Link>
      </div>

      <PageHeader
        title={machine.name}
        subtitle={`${machine.machine_code} · ${machine.machine_type} · ${machine.manufacturer || 'N/A'}`}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        {/* Machine Info */}
        <div className="card">
          <div className="card-header"><span className="card-title"><Cpu size={14} /> Machine Info</span></div>
          <table style={{ width: '100%', fontSize: 13 }}>
            <tbody>
              {[
                ['Code', <span className="mono">{machine.machine_code}</span>],
                ['Current State', <StatusBadge status={machine.current_state} />],
                ['Risk Score', <RiskBar score={machine.risk_score || 0} />],
                ['Status', <StatusBadge status={machine.status} />],
                ['Plant', <span className="mono" style={{ fontSize: 11 }}>{machine.plant_id?.slice(0, 8)}…</span>],
                ['Alarms', machine.alarm_count?.toLocaleString()],
                ['Incidents', machine.incident_count?.toLocaleString()],
                ['Commissioned', formatTimestamp(machine.commissioned_at)],
              ].map(([label, val]) => (
                <tr key={label}>
                  <td style={{ color: 'var(--color-text-muted)', padding: '5px 0', width: 140 }}>{label}</td>
                  <td style={{ color: 'var(--color-text-primary)', padding: '5px 0' }}>{val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Safety Zones & Interlocks */}
        <div className="card">
          <div className="card-header"><span className="card-title"><ShieldAlert size={14} /> Safety Zones & Interlocks</span></div>
          <div style={{ marginBottom: 12 }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Zones</div>
            {(machine.safety_zones || []).map(z => (
              <div key={z.id} style={{ marginBottom: 4 }}>
                <span className="mono" style={{ fontSize: 11 }}>{z.zone_code}</span>
                {' '}<span className="badge badge-info">{z.hazard_level}</span>
              </div>
            ))}
            {!machine.safety_zones?.length && <div style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>No zones</div>}
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: 6 }}>Interlocks</div>
            {(machine.interlocks || []).map(il => (
              <div key={il.id} style={{ marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Zap size={11} color="var(--color-warning)" />
                <span className="mono" style={{ fontSize: 11 }}>{il.interlock_code}</span>
                <StatusBadge status={il.current_state} />
                {il.is_required && <span className="badge badge-critical">Required</span>}
              </div>
            ))}
            {!machine.interlocks?.length && <div style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>No interlocks</div>}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Activity size={14} /> Machine Event Timeline</span>
        </div>
        {tl ? <LoadingSpinner text="Loading timeline..." /> : (
          <div className="timeline" style={{ marginTop: 12 }}>
            {(Array.isArray(timeline) ? timeline : []).slice(0, 30).map((item, i) => (
              <TimelineItem key={i} item={item} />
            ))}
            {(!timeline || timeline.length === 0) && (
              <div style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>No events recorded</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
