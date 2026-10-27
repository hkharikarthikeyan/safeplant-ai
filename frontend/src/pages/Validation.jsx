import React, { useState } from 'react';
import { ClipboardCheck, PlayCircle } from 'lucide-react';
import {
  PageHeader, LoadingSpinner, ErrorState, useApiData, formatTimestamp,
} from '../components/common';
import { runValidation, getValidationReports } from '../api';

export default function Validation() {
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState(null);
  const [selected, setSelected] = useState(null);
  const [refresh, setRefresh] = useState(0);

  const { data: reports, loading } = useApiData(() => getValidationReports({ per_page: 20 }), [refresh]);
  const items = Array.isArray(reports) ? reports : (reports?.items || []);

  const handleRun = async () => {
    setRunning(true);
    setRunMsg(null);
    try {
      const res = await runValidation({});
      const report = res.data?.data;
      setRunMsg({ success: true, msg: `Validation complete — ${report?.overall_status}: ${report?.passed_checks}/${report?.total_checks} checks passed` });
      setRefresh(r => r + 1);
    } catch (e) {
      setRunMsg({ success: false, msg: e.message });
    } finally {
      setRunning(false);
    }
  };

  const statusColor = (s) => s === 'PASS' ? 'var(--color-success)' : s === 'EXPECTED_ANOMALY' ? 'var(--color-info)' : s === 'FAIL' ? 'var(--color-critical)' : 'var(--color-warning)';

  return (
    <div className="page-container">
      <PageHeader
        title="Data Validation"
        subtitle="Automated integrity checks — 20+ validation rules"
        actions={
          <button className="btn btn-primary" onClick={handleRun} disabled={running}>
            <PlayCircle size={13} /> {running ? 'Running…' : 'Run Validation'}
          </button>
        }
      />

      {runMsg && (
        <div style={{
          padding: '10px 14px', borderRadius: 6, marginBottom: 16, fontSize: 12,
          background: runMsg.success ? 'var(--color-success-bg)' : 'var(--color-critical-bg)',
          color: runMsg.success ? 'var(--color-success)' : 'var(--color-critical)',
          border: `1px solid ${runMsg.success ? 'rgba(52,211,153,0.3)' : 'rgba(248,113,113,0.3)'}`,
        }}>
          {runMsg.success ? '✓' : '✗'} {runMsg.msg}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 16 }}>
        {/* Reports list */}
        <div className="card">
          <div className="card-header"><span className="card-title">Reports</span></div>
          {loading && <LoadingSpinner />}
          {items.map(r => (
            <div key={r.id} onClick={() => setSelected(r)}
              style={{
                padding: '10px 14px', borderRadius: 6, cursor: 'pointer', marginBottom: 4,
                background: selected?.id === r.id ? 'var(--color-bg-hover)' : 'transparent',
                border: `1px solid ${selected?.id === r.id ? 'var(--color-teal)' : 'transparent'}`,
              }}>
              <div style={{ fontWeight: 600, fontSize: 12, color: 'var(--color-text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>{r.run_code}</div>
              <div style={{ fontSize: 11, marginTop: 3, display: 'flex', gap: 8 }}>
                <span style={{ color: statusColor(r.overall_status) }}>{r.overall_status}</span>
                <span style={{ color: 'var(--color-text-muted)' }}>{r.passed_checks}/{r.total_checks} passed</span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>{formatTimestamp(r.started_at)}</div>
            </div>
          ))}
          {items.length === 0 && !loading && (
            <div style={{ color: 'var(--color-text-muted)', fontSize: 12, padding: 12 }}>No reports yet. Run validation first.</div>
          )}
        </div>

        {/* Report details */}
        <div className="card">
          {!selected ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--color-text-muted)' }}>
              <ClipboardCheck size={32} style={{ opacity: 0.2, marginBottom: 8 }} />
              Select a report to view details
            </div>
          ) : (
            <>
              <div className="card-header">
                <span className="card-title">{selected.run_code}</span>
                <span style={{ fontSize: 12, color: statusColor(selected.overall_status), fontWeight: 600 }}>
                  {selected.overall_status}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 20, marginBottom: 16, flexWrap: 'wrap' }}>
                {[
                  ['Total Checks', selected.total_checks],
                  ['Passed', selected.passed_checks, 'var(--color-success)'],
                  ['Failed', selected.failed_checks, 'var(--color-critical)'],
                  ['Expected Anomalies', selected.expected_anomalies, 'var(--color-info)'],
                  ['Unexpected Failures', selected.unexpected_failures, 'var(--color-warning)'],
                ].map(([k, v, color]) => (
                  <div key={k} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 10, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{k}</div>
                    <div style={{ fontSize: 22, fontWeight: 700, color: color || 'var(--color-text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>{v}</div>
                  </div>
                ))}
              </div>

              {/* Check results table */}
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr><th>Check Name</th><th>Status</th><th>Passed</th><th>Failed</th><th>Expected Anomaly</th></tr>
                  </thead>
                  <tbody>
                    {(selected.check_results || []).map((c, i) => (
                      <tr key={i}>
                        <td><span className="mono" style={{ fontSize: 11 }}>{c.check}</span></td>
                        <td>
                          <span style={{ color: statusColor(c.status), fontWeight: 600, fontSize: 11 }}>{c.status}</span>
                        </td>
                        <td style={{ color: 'var(--color-success)', fontSize: 12 }}>{c.passed}</td>
                        <td style={{ color: c.failed > 0 ? (c.is_expected_anomaly ? 'var(--color-info)' : 'var(--color-critical)') : 'var(--color-text-muted)', fontSize: 12 }}>{c.failed}</td>
                        <td>{c.is_expected_anomaly && <span className="badge badge-info">YES</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
