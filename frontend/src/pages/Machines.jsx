import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader, StatusBadge, RiskBar, LoadingSpinner, ErrorState,
  EmptyState, Pagination, useApiData, formatTimestamp,
} from '../components/common';
import { getMachines } from '../api';

const STATES = ['', 'RUNNING', 'IDLE', 'FAULT', 'EMERGENCY_STOP', 'MAINTENANCE', 'OFFLINE', 'STARTING', 'STOPPING'];

export default function Machines() {
  const [page, setPage] = useState(1);
  const [state, setState] = useState('');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('machine_code');

  const params = { page, per_page: 25, ...(state && { state }), ...(search && { search }), sort };
  const { data, loading, error } = useApiData(() => getMachines(params), [page, state, search, sort]);

  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  return (
    <div className="page-container">
      <PageHeader title="Machines" subtitle={`${meta?.total?.toLocaleString() || '—'} machines across all plants`} />

      <div className="filters-row">
        <input
          className="form-control"
          placeholder="Search machines..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
          style={{ width: 220 }}
        />
        <select className="form-control" value={state} onChange={e => { setState(e.target.value); setPage(1); }}>
          {STATES.map(s => <option key={s} value={s}>{s || 'All States'}</option>)}
        </select>
        <select className="form-control" value={sort} onChange={e => setSort(e.target.value)}>
          <option value="machine_code">Sort: Code</option>
          <option value="risk_score">Sort: Risk ↓</option>
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
                  <th>Code</th><th>Name</th><th>Type</th><th>State</th><th>Risk Score</th><th>Plant</th><th>Last Updated</th><th></th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={8}><EmptyState message="No machines found. Generate data first." /></td></tr>
                )}
                {items.map(machine => (
                  <tr key={machine.id}>
                    <td><span className="mono">{machine.machine_code}</span></td>
                    <td style={{ fontWeight: 500, color: 'var(--color-text-primary)', minWidth: 160 }}>{machine.name}</td>
                    <td style={{ fontSize: 11 }}>{machine.machine_type}</td>
                    <td><StatusBadge status={machine.current_state} /></td>
                    <td style={{ minWidth: 120 }}><RiskBar score={machine.risk_score || 0} /></td>
                    <td><span className="mono" style={{ fontSize: 11 }}>{machine.plant_id?.slice(0, 8)}…</span></td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>{formatTimestamp(machine.updated_at)}</td>
                    <td>
                      <Link to={`/machines/${machine.id}`} className="btn btn-secondary btn-sm">View</Link>
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
