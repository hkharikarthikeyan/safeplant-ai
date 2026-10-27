import React, { useState, useEffect } from 'react';
import { Database, PlayCircle, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import {
  PageHeader, StatusBadge, LoadingSpinner, ErrorState, useApiData, formatTimestamp,
} from '../components/common';
import { runGenerator, getGeneratorRuns } from '../api';

export default function DataGenerator() {
  const [mode, setMode] = useState('starter');
  const [seed, setSeed] = useState(20261022);
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState(null);
  const [refresh, setRefresh] = useState(0);

  const { data: runs, loading } = useApiData(() => getGeneratorRuns({ per_page: 10 }), [refresh]);
  const items = Array.isArray(runs) ? runs : (runs?.items || []);

  const handleRun = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const res = await runGenerator({ mode, seed });
      setRunMsg({ success: true, msg: `Generation started — Run: ${res.data?.data?.run_code}` });
      setTimeout(() => setRefresh(r => r + 1), 2000);
    } catch (e) {
      setRunMsg({ success: false, msg: e.message });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Data Generator"
        subtitle="Deterministic synthetic data generation with fixed seed 20261022"
      />

      {/* Generator Form */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header"><span className="card-title"><Database size={14} /> Launch Generation</span></div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16, marginBottom: 20 }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'block', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Mode</label>
            <select className="form-control" value={mode} onChange={e => setMode(e.target.value)} style={{ width: '100%' }}>
              <option value="starter">Starter (1 plant, 5 machines, 1K alarms)</option>
              <option value="full">Full (4 plants, 60 machines, 50K alarms)</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--color-text-muted)', display: 'block', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '0.4px' }}>Random Seed</label>
            <input
              className="form-control" type="number" value={seed}
              onChange={e => setSeed(parseInt(e.target.value))} style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Mode info cards */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
          {[
            { label: 'Starter Mode', items: ['1 Plant', '5 Machines', '4 Safety Zones', '5 Interlocks', '20 Alarm Defs', '1,000 Alarm Events', '~40 Incidents', '~80 Corrective Actions', '5 Anomaly Cases'] },
            { label: 'Full Mode', items: ['4 Plants', '60 Machines', '16 Safety Zones', '20 Interlocks', '200 Alarm Defs', '50,000 Alarm Events', '~2,000 Incidents', '~4,000 Corrective Actions', '5 Anomaly Cases (same)'] },
          ].map(({ label, items }) => (
            <div key={label} style={{ background: 'var(--color-bg-secondary)', borderRadius: 8, padding: '14px 16px' }}>
              <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--color-text-primary)', fontSize: 13 }}>{label}</div>
              {items.map(i => (
                <div key={i} style={{ fontSize: 12, color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                  <span style={{ color: 'var(--color-teal)', marginRight: 6 }}>✓</span>{i}
                </div>
              ))}
            </div>
          ))}
        </div>

        <div style={{ background: 'var(--color-warning-bg)', border: '1px solid rgba(251,191,36,0.3)', borderRadius: 6, padding: '10px 14px', marginBottom: 16, fontSize: 12, color: 'var(--color-warning)' }}>
          ⚠ Generation period: <strong>2026-10-01 → 2026-10-30 UTC</strong> · Seed <strong>{seed}</strong> produces identical output every run · Full mode may take 2–5 minutes
        </div>

        {runMsg && (
          <div style={{
            padding: '10px 14px', borderRadius: 6, marginBottom: 12, fontSize: 12,
            background: runMsg.success ? 'var(--color-success-bg)' : 'var(--color-critical-bg)',
            color: runMsg.success ? 'var(--color-success)' : 'var(--color-critical)',
            border: `1px solid ${runMsg.success ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)'}`,
          }}>
            {runMsg.success ? '✓' : '✗'} {runMsg.msg}
          </div>
        )}

        <button className="btn btn-primary" onClick={handleRun} disabled={running}>
          <PlayCircle size={14} /> {running ? 'Starting Generation…' : `Run ${mode.toUpperCase()} Generation`}
        </button>
      </div>

      {/* Generation History */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Generation History</span>
          <button className="btn btn-secondary btn-sm" onClick={() => setRefresh(r => r + 1)}>↺ Refresh</button>
        </div>
        {loading && <LoadingSpinner />}
        {!loading && (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run Code</th><th>Mode</th><th>Seed</th><th>Status</th>
                  <th>Entities</th><th>Checksum</th><th>Started</th><th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={8} style={{ padding: 30, textAlign: 'center', color: 'var(--color-text-muted)' }}>No generation runs yet</td></tr>
                )}
                {items.map(run => {
                  const duration = run.completed_at && run.started_at
                    ? Math.round((new Date(run.completed_at) - new Date(run.started_at)) / 1000)
                    : null;
                  const totalEntities = run.entity_counts
                    ? Object.values(run.entity_counts).reduce((a, b) => a + b, 0)
                    : null;
                  return (
                    <tr key={run.id}>
                      <td><span className="mono" style={{ fontSize: 11 }}>{run.run_code}</span></td>
                      <td><span className="badge badge-info">{run.mode?.toUpperCase()}</span></td>
                      <td><span className="mono">{run.seed}</span></td>
                      <td>
                        <StatusBadge status={run.status} />
                        {run.status === 'RUNNING' && <span className="spinner" style={{ width: 12, height: 12, marginLeft: 8 }} />}
                      </td>
                      <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12 }}>
                        {totalEntities?.toLocaleString() || '—'}
                      </td>
                      <td><span className="mono" style={{ fontSize: 10 }}>{run.checksum?.slice(0, 10) || '—'}</span></td>
                      <td style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>{formatTimestamp(run.started_at)}</td>
                      <td style={{ fontSize: 12 }}>{duration != null ? `${duration}s` : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
