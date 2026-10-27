import React, { useEffect, useRef, useState } from 'react';

export function LoadingSpinner({ text = 'Loading...' }) {
  return (
    <div className="loading-spinner">
      <div className="spinner" />
      <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>{text}</span>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div className="error-state">
      ⚠ {message || 'An error occurred. Please try again.'}
    </div>
  );
}

export function EmptyState({ message = 'No data available', icon }) {
  return (
    <div className="empty-state">
      <div style={{ fontSize: 32, opacity: 0.3 }}>{icon || '📭'}</div>
      <div style={{ fontSize: 14 }}>{message}</div>
    </div>
  );
}

export function SeverityBadge({ severity }) {
  const cls = {
    CRITICAL: 'badge-critical',
    HIGH: 'badge-high',
    MEDIUM: 'badge-medium',
    LOW: 'badge-low',
  }[severity] || 'badge-muted';
  return <span className={`badge ${cls}`}>{severity}</span>;
}

export function StatusBadge({ status }) {
  const cls = {
    OPEN: 'badge-critical',
    INVESTIGATING: 'badge-high',
    ACTION_REQUIRED: 'badge-medium',
    VERIFICATION_PENDING: 'badge-info',
    CLOSED: 'badge-success',
    REOPENED: 'badge-high',
    ON_TIME: 'badge-success',
    DELAYED: 'badge-high',
    MISSING: 'badge-critical',
    INVALID: 'badge-critical',
    PENDING: 'badge-info',
    ACTIVE: 'badge-success',
    RUNNING: 'badge-success',
    FAULT: 'badge-critical',
    EMERGENCY_STOP: 'badge-critical',
    MAINTENANCE: 'badge-medium',
    IDLE: 'badge-info',
    OFFLINE: 'badge-muted',
    COMPLETED: 'badge-success',
    VERIFIED: 'badge-success',
  }[status] || 'badge-muted';
  return <span className={`badge ${cls}`}>{status?.replace(/_/g, ' ')}</span>;
}

function useCountUp(target, duration = 800) {
  const [display, setDisplay] = useState(0);
  const raf = useRef(null);
  useEffect(() => {
    if (typeof target !== 'number') return;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / duration, 1);
      setDisplay(Math.round(p * target));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, duration]);
  return display;
}

export function KpiCard({ label, value, variant = 'info', icon: Icon }) {
  const num = typeof value === 'number' ? value : null;
  const counted = useCountUp(num ?? 0);
  const display = num !== null ? counted.toLocaleString() : (value ?? '—');
  return (
    <div className={`kpi-card ${variant}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{display}</div>
      {Icon && <div className="kpi-icon"><Icon size={40} /></div>}
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
    </div>
  );
}

export function Pagination({ meta, page, setPage }) {
  if (!meta || meta.pages <= 1) return null;
  return (
    <div className="pagination">
      <span className="pagination-info">
        {(page - 1) * meta.per_page + 1}–{Math.min(page * meta.per_page, meta.total)} of {meta.total?.toLocaleString()}
      </span>
      <button className="btn btn-secondary btn-sm" disabled={!meta.has_prev} onClick={() => setPage(p => p - 1)}>← Prev</button>
      <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>Page {page} / {meta.pages}</span>
      <button className="btn btn-secondary btn-sm" disabled={!meta.has_next} onClick={() => setPage(p => p + 1)}>Next →</button>
    </div>
  );
}

export function RiskBar({ score }) {
  const cls = score >= 70 ? 'risk-critical' : score >= 40 ? 'risk-high' : score >= 20 ? 'risk-medium' : 'risk-low';
  return (
    <div>
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)' }}>{score?.toFixed(1)}</span>
      <div className="risk-bar">
        <div className={`risk-bar-fill ${cls}`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
    </div>
  );
}

export function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
      {payload.map((entry, i) => (
        <div key={i} style={{ color: entry.color, fontSize: 12 }}>
          {entry.name}: {entry.value?.toLocaleString()}
        </div>
      ))}
    </div>
  );
}

export function formatTimestamp(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function useApiData(fetchFn, deps = []) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchFn()
      .then(res => { if (!cancelled) setData(res.data?.data ?? res.data); })
      .catch(err => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}
