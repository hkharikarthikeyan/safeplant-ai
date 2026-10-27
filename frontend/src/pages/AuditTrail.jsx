import React, { useState } from 'react';
import { RefreshCw, Database } from 'lucide-react';
import {
  PageHeader, LoadingSpinner, ErrorState, Pagination, formatTimestamp, useApiData,
} from '../components/common';
import { getAuditLogs } from '../api';
import api from '../api';

export default function AuditTrail() {
  const [page, setPage] = useState(1);
  const [entityType, setEntityType] = useState('');
  const [backfilling, setBackfilling] = useState(false);
  const [backfillResult, setBackfillResult] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const params = { page, per_page: 50, ...(entityType && { entity_type: entityType }) };
  const { data, loading, error } = useApiData(
    () => getAuditLogs(params),
    [page, entityType, refreshKey]
  );
  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  const ENTITY_TYPES = ['', 'Incident', 'CorrectiveAction', 'Machine', 'Acknowledgement'];

  const handleBackfill = async () => {
    setBackfilling(true);
    setBackfillResult(null);
    try {
      const res = await api.post('/audit-logs/backfill');
      setBackfillResult(res.data?.data);
      setPage(1);
      setRefreshKey(k => k + 1);
    } catch (e) {
      setBackfillResult({ error: e.message });
    } finally {
      setBackfilling(false);
    }
  };

  return (
    <div className="page-container">
      <PageHeader
        title="Audit Trail"
        subtitle="Complete, immutable audit log of all safety-critical events"
        actions={
          <button className="btn btn-secondary btn-sm" onClick={handleBackfill} disabled={backfilling}>
            {backfilling ? <><RefreshCw size={13} style={{ animation: 'spin 0.8s linear infinite' }} /> Backfilling…</> : <><Database size={13} /> Backfill from Events</>}
          </button>
        }
      />

      {backfillResult && !backfillResult.error && (
        <div style={{
          background: 'var(--color-success-bg)', border: '1px solid var(--color-success)',
          borderRadius: 8, padding: '10px 16px', marginBottom: 16, fontSize: 13,
          color: 'var(--color-success)', display: 'flex', gap: 16, flexWrap: 'wrap',
        }}>
          <strong>✓ Backfill complete — {backfillResult.backfilled?.toLocaleString()} entries written</strong>
          {Object.entries(backfillResult.breakdown || {}).map(([k, v]) => (
            <span key={k} style={{ color: 'var(--color-text-secondary)' }}>
              {k.replace(/_/g, ' ')}: <strong>{v}</strong>
            </span>
          ))}
        </div>
      )}
      {backfillResult?.error && (
        <div className="error-state" style={{ marginBottom: 16 }}>Backfill failed: {backfillResult.error}</div>
      )}

      <div className="filters-row">
        <select className="form-control" value={entityType} onChange={e => { setEntityType(e.target.value); setPage(1); }}>
          {ENTITY_TYPES.map(t => <option key={t} value={t}>{t || 'All Entity Types'}</option>)}
        </select>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Entity Type</th>
                  <th>Entity ID</th>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>Before → After</th>
                </tr>
              </thead>
              <tbody>
                {items.map(log => (
                  <tr key={log.id}>
                    <td style={{ fontSize: 11, color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                      {formatTimestamp(log.occurred_at)}
                    </td>
                    <td>
                      <span className={`badge ${ENTITY_TYPE_BADGE[log.entity_type] || 'badge-muted'}`} style={{ fontSize: 10 }}>
                        {log.entity_type}
                      </span>
                    </td>
                    <td><span className="mono" style={{ fontSize: 10 }}>{log.entity_id?.slice(0, 12)}…</span></td>
                    <td style={{ fontWeight: 600, fontSize: 12 }}>{log.action}</td>
                    <td style={{ fontSize: 12 }}>{log.actor || 'SYSTEM'}</td>
                    <td style={{ fontSize: 11, maxWidth: 300 }}>
                      {log.before_state || log.after_state ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                          {log.before_state && (
                            <span style={{ color: 'var(--color-high)' }}>{formatState(log.before_state)}</span>
                          )}
                          {log.before_state && log.after_state && (
                            <span style={{ color: 'var(--color-text-muted)' }}>→</span>
                          )}
                          {log.after_state && (
                            <span style={{ color: 'var(--color-success)' }}>{formatState(log.after_state)}</span>
                          )}
                        </span>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
                      No audit logs yet. Click <strong>Backfill from Events</strong> to populate from existing data.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <Pagination meta={meta} page={page} setPage={setPage} />
        </>
      )}
    </div>
  );
}

const ENTITY_TYPE_BADGE = {
  Incident: 'badge-critical',
  CorrectiveAction: 'badge-medium',
  Machine: 'badge-info',
  Acknowledgement: 'badge-success',
};

// Converts {status: 'OPEN', notes: 'foo'} → 'OPEN · foo'
function formatState(obj) {
  if (!obj || typeof obj !== 'object') return String(obj);
  const priority = ['status', 'state', 'ack_status'];
  const parts = [];
  for (const key of priority) {
    if (obj[key] != null) parts.push(obj[key]);
  }
  for (const [k, v] of Object.entries(obj)) {
    if (priority.includes(k) || v == null || v === '') continue;
    if (k === 'notes') parts.push(v);
    else if (k === 'valid' || k === 'trigger') parts.push(`${k}: ${v}`);
    else if (k === 'ack_code') parts.push(v);
  }
  return parts.join(' · ') || JSON.stringify(obj);
}
