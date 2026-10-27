import React from 'react';
import { PageHeader, SeverityBadge, LoadingSpinner, ErrorState, useApiData } from '../components/common';
import { getAlarmDefinitions } from '../api';

export default function AlarmDefinitions() {
  const { data, loading, error } = useApiData(() => getAlarmDefinitions({ per_page: 50 }));
  const items = Array.isArray(data) ? data : (data?.items || []);

  const ACK_DEADLINES = { CRITICAL: 120, HIGH: 300, MEDIUM: 900, LOW: 1800 };

  return (
    <div className="page-container">
      <PageHeader title="Alarm Definitions" subtitle={`${items.length} alarm definitions configured`} />
      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th><th>Name</th><th>Category</th><th>Severity</th>
                <th>Threshold</th><th>Ack Deadline</th><th>Active</th>
              </tr>
            </thead>
            <tbody>
              {items.map(d => (
                <tr key={d.id}>
                  <td><span className="mono" style={{ fontSize: 11 }}>{d.alarm_code}</span></td>
                  <td style={{ fontWeight: 500, maxWidth: 200 }}>{d.name}</td>
                  <td><span className="badge badge-muted">{d.category}</span></td>
                  <td><SeverityBadge severity={d.severity} /></td>
                  <td style={{ fontSize: 12 }}>{d.threshold_value} {d.threshold_unit}</td>
                  <td style={{ fontSize: 12 }}>
                    <span style={{ color: d.severity === 'CRITICAL' ? 'var(--color-critical)' : 'var(--color-text-secondary)' }}>
                      {d.ack_deadline_seconds}s
                    </span>
                  </td>
                  <td>{d.is_active ? <span className="badge badge-success">YES</span> : <span className="badge badge-muted">NO</span>}</td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>No alarm definitions. Generate data first.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
