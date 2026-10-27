import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader, SeverityBadge, StatusBadge, LoadingSpinner, ErrorState,
  EmptyState, Pagination, useApiData, formatTimestamp,
} from '../components/common';
import { getIncidents } from '../api';

const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const STATUSES = ['', 'OPEN', 'INVESTIGATING', 'ACTION_REQUIRED', 'VERIFICATION_PENDING', 'CLOSED', 'REOPENED'];

export default function Incidents() {
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState('');
  const [status, setStatus] = useState('');

  const params = { page, per_page: 25, ...(severity && { severity }), ...(status && { status }) };
  const { data, loading, error } = useApiData(() => getIncidents(params), [page, severity, status]);

  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  return (
    <div className="page-container">
      <PageHeader title="Incidents" subtitle={`${meta?.total?.toLocaleString() || '—'} safety incidents`} />

      <div className="filters-row">
        <select className="form-control" value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}>
          {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
        </select>
        <select className="form-control" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
          {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
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
                  <th>Code</th><th>Severity</th><th>Status</th><th>Engineer</th>
                  <th>Detected</th><th>Missing Context</th><th></th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={7}><EmptyState message="No incidents found." /></td></tr>
                )}
                {items.map(inc => (
                  <tr key={inc.id} style={inc.has_missing_context ? { background: 'rgba(248,113,113,0.04)' } : {}}>
                    <td><span className="mono">{inc.incident_code}</span></td>
                    <td><SeverityBadge severity={inc.severity} /></td>
                    <td><StatusBadge status={inc.status} /></td>
                    <td style={{ fontSize: 12 }}>{inc.assigned_engineer || '—'}</td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>{formatTimestamp(inc.detected_at)}</td>
                    <td>
                      {inc.has_missing_context && (
                        <span className="badge badge-critical" title="Case 3: Incident has no triggering alarm context">⚠ CASE 3</span>
                      )}
                    </td>
                    <td>
                      <Link to={`/incidents/${inc.id}`} className="btn btn-secondary btn-sm">View</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination meta={meta} page={page} setPage={setPage} />
        </>
      )}
    </div>
  );
}
