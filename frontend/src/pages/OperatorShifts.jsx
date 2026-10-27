import React, { useState } from 'react';
import {
  PageHeader, StatusBadge, LoadingSpinner, ErrorState,
  Pagination, formatTimestamp, useApiData,
} from '../components/common';
import { getOperatorShifts } from '../api';

export default function OperatorShifts() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useApiData(() => getOperatorShifts({ page, per_page: 50 }), [page]);
  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  return (
    <div className="page-container">
      <PageHeader title="Operator Shifts" subtitle={`${meta?.total?.toLocaleString() || '—'} recorded operator shifts`} />
      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr><th>Code</th><th>Operator</th><th>Shift Type</th><th>Start</th><th>End</th><th>Status</th></tr>
              </thead>
              <tbody>
                {items.map(s => (
                  <tr key={s.id}>
                    <td><span className="mono" style={{ fontSize: 11 }}>{s.shift_code}</span></td>
                    <td style={{ fontWeight: 500 }}>{s.operator_name}</td>
                    <td>
                      <span className={`badge ${s.shift_type === 'NIGHT' ? 'badge-muted' : s.shift_type === 'EVENING' ? 'badge-medium' : 'badge-info'}`}>
                        {s.shift_type}
                      </span>
                    </td>
                    <td style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{formatTimestamp(s.shift_start)}</td>
                    <td style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{formatTimestamp(s.shift_end)}</td>
                    <td><StatusBadge status={s.status} /></td>
                  </tr>
                ))}
                {items.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>No shifts. Generate data first.</td></tr>}
              </tbody>
            </table>
          </div>
          <Pagination meta={meta} page={page} setPage={setPage} />
        </>
      )}
    </div>
  );
}
