import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Factory } from 'lucide-react';
import {
  PageHeader, StatusBadge, LoadingSpinner, ErrorState, EmptyState, Pagination, useApiData
} from '../components/common';
import { getPlants } from '../api';

export default function Plants() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useApiData(() => getPlants({ page, per_page: 20 }), [page]);

  return (
    <div className="page-container">
      <PageHeader title="Plants" subtitle="All registered industrial plants" />
      {loading && <LoadingSpinner />}
      {error && <ErrorState message={error} />}
      {data && (
        <>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th><th>Name</th><th>Location</th><th>Region</th><th>Timezone</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.items?.length === 0 && (
                  <tr><td colSpan={6}><EmptyState message="No plants found. Generate data first." icon={<Factory size={24} />} /></td></tr>
                )}
                {(data.items || data).map?.(plant => (
                  <tr key={plant.id}>
                    <td><span className="mono">{plant.plant_code}</span></td>
                    <td style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>{plant.name}</td>
                    <td>{plant.location}</td>
                    <td>{plant.region}</td>
                    <td>{plant.timezone}</td>
                    <td><StatusBadge status={plant.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination meta={data.meta || data} page={page} setPage={setPage} />
        </>
      )}
    </div>
  );
}
