import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  PageHeader, SeverityBadge, StatusBadge, LoadingSpinner, ErrorState,
  EmptyState, Pagination, useApiData, formatTimestamp,
} from '../components/common';
import { getAlarms } from '../api';

const SEVERITIES = ['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const ACK_STATUSES = ['', 'PENDING', 'ON_TIME', 'DELAYED', 'MISSING', 'INVALID'];

export default function Alarms() {
  const [page, setPage] = useState(1);
  const [severity, setSeverity] = useState('');
  const [ackStatus, setAckStatus] = useState('');
  const [isReplayed, setIsReplayed] = useState('');

  const params = {
    page, per_page: 50,
    ...(severity && { severity }),
    ...(ackStatus && { ack_status: ackStatus }),
    ...(isReplayed !== '' && { is_replayed: isReplayed }),
  };
  const { data, loading, error } = useApiData(() => getAlarms(params), [page, severity, ackStatus, isReplayed]);

  const items = Array.isArray(data) ? data : (data?.items || []);
  const meta = Array.isArray(data) ? null : data?.meta;

  return (
    <div className="page-container">
      <PageHeader title="Alarm Events" subtitle={`${meta?.total?.toLocaleString() || '—'} total alarm events`} />

      <div className="filters-row">
        <select className="form-control" value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}>
          {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
        </select>
        <select className="form-control" value={ackStatus} onChange={e => { setAckStatus(e.target.value); setPage(1); }}>
          {ACK_STATUSES.map(s => <option key={s} value={s}>{s || 'All Ack Statuses'}</option>)}
        </select>
        <select className="form-control" value={isReplayed} onChange={e => { setIsReplayed(e.target.value); setPage(1); }}>
          <option value="">All</option>
          <option value="false">Original</option>
          <option value="true">Replayed (Case 4)</option>
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
                  <th>Event Code</th><th>Severity</th><th>Ack Status</th>
                  <th>Timestamp</th><th>Status</th><th>Replayed</th><th></th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 && (
                  <tr><td colSpan={7}><EmptyState message="No alarms found. Generate data first." /></td></tr>
                )}
                {items.map(alarm => (
                  <tr key={alarm.id} style={alarm.is_replayed ? { background: 'rgba(96,165,250,0.04)' } : {}}>
                    <td><span className="mono" style={{ fontSize: 11 }}>{alarm.alarm_event_code}</span></td>
                    <td><SeverityBadge severity={alarm.severity} /></td>
                    <td><StatusBadge status={alarm.acknowledgement_status} /></td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: 11 }}>{formatTimestamp(alarm.alarm_timestamp)}</td>
                    <td><StatusBadge status={alarm.status} /></td>
                    <td>
                      {alarm.is_replayed && <span className="badge badge-info">REPLAY</span>}
                    </td>
                    <td>
                      <Link to={`/alarms/${alarm.id}`} className="btn btn-secondary btn-sm">View</Link>
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
