import React from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  PageHeader, LoadingSpinner, ErrorState, CustomTooltip, useApiData,
} from '../components/common';
import {
  getAlarmTrends, getSeverityDistribution, getMachineRisk,
  getRepeatedConditions, getAckAnalytics, getIncidentAnalytics,
  getActionAnalytics, getShiftPerformance,
} from '../api';

const COLORS = ['#f87171', '#fb923c', '#fbbf24', '#34d399', '#38bdf8', '#a78bfa'];

function Section({ title, children }) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="card-header"><span className="card-title">{title}</span></div>
      {children}
    </div>
  );
}

export default function Analytics() {
  const { data: trends, loading: tl } = useApiData(() => getAlarmTrends(30));
  const { data: severity, loading: sl } = useApiData(getSeverityDistribution);
  const { data: risk, loading: rl } = useApiData(() => getMachineRisk(10));
  const { data: ack, loading: al } = useApiData(getAckAnalytics);
  const { data: incidents, loading: il } = useApiData(getIncidentAnalytics);
  const { data: actions, loading: acl } = useApiData(getActionAnalytics);
  const { data: shifts, loading: shl } = useApiData(getShiftPerformance);
  const { data: repeated } = useApiData(getRepeatedConditions);

  const trendData = Array.isArray(trends) ? trends : [];
  const severityData = Array.isArray(severity) ? severity : [];
  const riskData = Array.isArray(risk) ? risk : [];
  const ackData = ack?.by_severity || [];
  const incidentByStatus = incidents?.by_status || [];
  const incidentBySeverity = incidents?.by_severity || [];
  const actionByStatus = actions?.by_status || [];
  const shiftData = Array.isArray(shifts) ? shifts : [];

  return (
    <div className="page-container">
      <PageHeader title="Analytics" subtitle="Safety intelligence metrics and trend analysis" />

      {/* Alarm Trends */}
      <Section title="Alarm Trend — Last 30 Days">
        {tl ? <LoadingSpinner /> : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d?.slice(5)} stroke="var(--color-border)" />
              <YAxis tick={{ fontSize: 10 }} stroke="var(--color-border)" />
              <Tooltip content={<CustomTooltip />} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="CRITICAL" stroke="#f87171" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="HIGH" stroke="#fb923c" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="MEDIUM" stroke="#fbbf24" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="LOW" stroke="#34d399" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Section>

      <div className="charts-grid">
        {/* Severity Distribution */}
        <Section title="Alarm Severity Distribution">
          {sl ? <LoadingSpinner /> : (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={severityData} dataKey="count" nameKey="severity" cx="50%" cy="50%" outerRadius={80}>
                  {severityData.map((entry, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(val) => val.toLocaleString()} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }}
                  formatter={(val) => severityData.find(d => d.severity === val)?.severity || val} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Section>

        {/* Incident Status */}
        <Section title="Incidents by Status">
          {il ? <LoadingSpinner /> : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={incidentByStatus} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis type="number" tick={{ fontSize: 10 }} stroke="var(--color-border)" />
                <YAxis type="category" dataKey="status" tick={{ fontSize: 10 }} width={120} stroke="var(--color-border)" />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#38bdf8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>
      </div>

      {/* Acknowledgement Compliance */}
      <Section title="Acknowledgement Compliance by Severity">
        {al ? <LoadingSpinner /> : (
          <>
            <div style={{ display: 'flex', gap: 24, marginBottom: 16, flexWrap: 'wrap' }}>
              {ack && [
                ['Total Alarms', ack.total_alarms?.toLocaleString()],
                ['On-Time', ack.on_time?.toLocaleString()],
                ['Delayed', ack.delayed?.toLocaleString()],
                ['Missing', ack.missing?.toLocaleString()],
                ['Compliance Rate', `${(ack.compliance_rate * 100).toFixed(1)}%`],
                ['Mean Response', `${ack.mean_response_time_seconds?.toFixed(0)}s`],
              ].map(([k, v]) => (
                <div key={k} style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{k}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-primary)', fontFamily: 'JetBrains Mono, monospace' }}>{v}</div>
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={ackData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="severity" tick={{ fontSize: 10 }} stroke="var(--color-border)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--color-border)" tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                <Tooltip content={<CustomTooltip />} formatter={v => `${(v * 100).toFixed(1)}%`} />
                <Bar dataKey="compliance_rate" name="Compliance Rate" fill="#2dd4bf" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
      </Section>

      <div className="charts-grid">
        {/* Shift Performance */}
        <Section title="Acknowledgement Compliance by Shift">
          {shl ? <LoadingSpinner /> : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={shiftData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="shift_type" tick={{ fontSize: 11 }} stroke="var(--color-border)" />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--color-border)" tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                <Tooltip content={<CustomTooltip />} formatter={v => `${(v * 100).toFixed(1)}%`} />
                <Bar dataKey="compliance_rate" name="Compliance" fill="#a78bfa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Section>

        {/* Corrective Action Status */}
        <Section title="Corrective Action Status">
          {acl ? <LoadingSpinner /> : (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={actionByStatus} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={70} innerRadius={40}>
                  {actionByStatus.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={v => v.toLocaleString()} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 10 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Section>
      </div>

      {/* Repeated Unsafe Conditions */}
      {repeated && repeated.length > 0 && (
        <Section title={`Repeated Unsafe Conditions (${repeated.length} machine-zone pairs)`}>
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr><th>Machine Code</th><th>Safety Zone</th><th>Incident Count</th><th>Rule</th><th>Severity</th></tr>
              </thead>
              <tbody>
                {repeated.map((r, i) => (
                  <tr key={i}>
                    <td><span className="mono" style={{ fontSize: 11 }}>{r.machine_code}</span></td>
                    <td><span className="mono" style={{ fontSize: 11 }}>{r.safety_zone_id?.slice(0, 8)}…</span></td>
                    <td style={{ fontWeight: 700, color: 'var(--color-warning)' }}>{r.incident_count}</td>
                    <td><span className="mono" style={{ fontSize: 11 }}>{r.rule_id}</span></td>
                    <td><span className={`badge badge-medium`}>{r.severity}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      )}
    </div>
  );
}
