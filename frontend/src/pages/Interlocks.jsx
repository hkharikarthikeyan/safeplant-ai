import React from 'react';
import { PageHeader, StatusBadge, LoadingSpinner, ErrorState, useApiData } from '../components/common';
import { getInterlocks } from '../api';

export default function Interlocks() {
  const { data, loading, error } = useApiData(() => getInterlocks({ per_page: 50 }));
  const items = Array.isArray(data) ? data : (data?.items || []);

  return (
    <div className="page-container">
      <PageHeader title="Interlocks" subtitle="Safety interlock devices and current states" />
      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr><th>Code</th><th>Name</th><th>Type</th><th>Current State</th><th>Safety Critical</th><th>Plant</th></tr>
            </thead>
            <tbody>
              {items.map(il => (
                <tr key={il.id}>
                  <td><span className="mono">{il.interlock_code}</span></td>
                  <td style={{ fontWeight: 500 }}>{il.name}</td>
                  <td style={{ fontSize: 11 }}>{il.interlock_type?.replace(/_/g, ' ')}</td>
                  <td><StatusBadge status={il.current_state} /></td>
                  <td>{il.is_safety_critical ? <span className="badge badge-critical">YES</span> : <span className="badge badge-muted">NO</span>}</td>
                  <td><span className="mono" style={{ fontSize: 11 }}>{il.plant_id?.slice(0, 8)}…</span></td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>No interlocks. Generate data first.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
