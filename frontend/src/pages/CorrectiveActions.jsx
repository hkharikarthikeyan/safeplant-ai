import React, { useState } from 'react';
import {
  PageHeader, StatusBadge, SeverityBadge, LoadingSpinner, ErrorState,
  EmptyState, Pagination, formatTimestamp, useApiData,
} from '../components/common';
import { getCorrectiveActions } from '../api';

export default function CorrectiveActions() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState('');
  const [overdue, setOverdue] = useState(false);

  const params = { page, per_page: 25, ...(status && { status }), ...(overdue && { overdue: true }) };
  const { data, loading, error } = useApiData(() => getCorrectiveActions(params), [page, status, overdue]);

  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  const now = new Date();

  return (
    <div className="page-container">
      <PageHeader title="Corrective Actions" subtitle={`${meta?.total?.toLocaleString() || '—'} actions across all incidents`} />

      <div className="filters-row">
        <select className="form-control" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
          {['', 'OPEN', 'IN_PROGRESS', 'COMPLETED', 'VERIFICATION_PENDING', 'VERIFIED', 'CLOSED', 'REOPENED']
            .map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
          <input type="checkbox" checked={overdue} onChange={e => { setOverdue(e.target.checked); setPage(1); }} />
          Overdue Only
        </label>
      </div>

      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th><th>Status</th><th>Priority</th><th>Engineer</th>
                  <th>Due Date</th><th>Overdue</th><th>Verified</th><th>Anomaly</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={8}><EmptyState message="No corrective actions found." /></td></tr>
                )}
                {items.map(ca => {
                  const isDue = ca.due_at && new Date(ca.due_at) < now && !['VERIFIED', 'CLOSED'].includes(ca.status);
                  return (
                    <tr key={ca.id} style={ca.is_closed_without_verification ? { background: 'rgba(248,113,113,0.05)' } : isDue ? { background: 'rgba(251,191,36,0.05)' } : {}}>
                      <td><span className="mono" style={{ fontSize: 11 }}>{ca.action_code}</span></td>
                      <td><StatusBadge status={ca.status} /></td>
                      <td><SeverityBadge severity={ca.priority} /></td>
                      <td style={{ fontSize: 12 }}>{ca.assigned_engineer || '—'}</td>
                      <td style={{ color: isDue ? 'var(--color-warning)' : 'var(--color-text-muted)', fontSize: 11 }}>
                        {formatTimestamp(ca.due_at)}
                      </td>
                      <td>{isDue && <span className="badge badge-medium">OVERDUE</span>}</td>
                      <td>{ca.verification_result && <span className={`badge ${ca.verification_result === 'PASS' ? 'badge-success' : 'badge-critical'}`}>{ca.verification_result}</span>}</td>
                      <td>{ca.is_closed_without_verification && <span className="badge badge-critical" title="Case 5: Closed without verification">CASE 5</span>}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Pagination meta={meta} page={page} setPage={setPage} />
        </>
      )}
    </div>
  );
}
