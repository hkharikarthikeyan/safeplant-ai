import React, { useState } from 'react';
import { PageHeader, LoadingSpinner, ErrorState, formatTimestamp, useApiData } from '../components/common';
import { getSafetyZones } from '../api';

export default function SafetyZones() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useApiData(() => getSafetyZones({ page, per_page: 30 }), [page]);
  const items = Array.isArray(data) ? data : (data?.items || []);

  return (
    <div className="page-container">
      <PageHeader title="Safety Zones" subtitle="All plant safety zones and hazard levels" />
      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {!loading && !error && (
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr><th>Code</th><th>Name</th><th>Type</th><th>Hazard Level</th><th>Plant</th><th>Active</th></tr>
            </thead>
            <tbody>
              {items.map(z => (
                <tr key={z.id}>
                  <td><span className="mono">{z.zone_code}</span></td>
                  <td style={{ fontWeight: 500 }}>{z.name}</td>
                  <td><span className="badge badge-muted">{z.zone_type}</span></td>
                  <td><span className={`badge ${z.hazard_level === 'CRITICAL' ? 'badge-critical' : z.hazard_level === 'HIGH' ? 'badge-high' : z.hazard_level === 'MEDIUM' ? 'badge-medium' : 'badge-success'}`}>{z.hazard_level}</span></td>
                  <td><span className="mono" style={{ fontSize: 11 }}>{z.plant_id?.slice(0, 8)}…</span></td>
                  <td>{z.is_active ? <span className="badge badge-success">YES</span> : <span className="badge badge-muted">NO</span>}</td>
                </tr>
              ))}
              {items.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-muted)' }}>No zones. Generate data first.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
