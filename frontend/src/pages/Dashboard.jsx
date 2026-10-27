import React, { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {
  Factory, Cpu, BellRing, AlertTriangle, ShieldOff, Clock, RefreshCw, CheckSquare,
} from 'lucide-react';
import {
  KpiCard, SeverityBadge, StatusBadge, LoadingSpinner,
  ErrorState, CustomTooltip, PageHeader, formatTimestamp,
} from '../components/common';
import { getDashboardSummary, getDashboardTrends, getMachineRisk } from '../api';

const SEVERITY_COLORS = {
  CRITICAL: '#f87171',
  HIGH: '#fb923c',
  MEDIUM: '#fbbf24',
  LOW: '#34d399',
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [riskScores, setRiskScores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, trendRes, riskRes] = await Promise.all([
        getDashboardSummary(),
        getDashboardTrends(30),
        getMachineRisk(10),
      ]);
      setSummary(sumRes.data?.data);
      setTrends(trendRes.data?.data || []);
      setRiskScores(riskRes.data?.data || []);
      setLastRefresh(new Date());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  if (loading) return <div className="page-container"><LoadingSpinner text="Loading dashboard..." /></div>;
  if (error) return <div className="page-container"><ErrorState message={error} /></div>;

  const kpis = summary?.kpis || {};
  const recentCritical = summary?.recent_critical_events || [];

  // Severity pie data
  const severityPie = [
    { name: 'Critical', value: kpis.critical_alarms || 0, color: '#f87171' },
    { name: 'Other', value: Math.max(0, (kpis.total_alarms || 0) - (kpis.critical_alarms || 0)), color: '#38bdf8' },
  ];

  return (
    <div className="page-container">
      <PageHeader
        title="Operations Dashboard"
        subtitle={`SafePlant AI — Industrial Safety Intelligence · Last updated ${lastRefresh.toLocaleTimeString()}`}
        actions={
          <button className="btn btn-secondary btn-sm" onClick={fetchAll}>
            <RefreshCw size={13} /> Refresh
          </button>
        }
      />

      {/* KPI Cards */}
      <div className="kpi-grid">
        <KpiCard label="Total Plants" value={kpis.total_plants} variant="info" icon={Factory} />
        <KpiCard label="Total Machines" value={kpis.total_machines} variant="teal" icon={Cpu} />
        <KpiCard label="Total Alarms" value={kpis.total_alarms} variant="info" icon={BellRing} />
        <KpiCard label="Critical Alarms" value={kpis.critical_alarms} variant="critical" icon={AlertTriangle} />
        <KpiCard label="Open Incidents" value={kpis.open_incidents} variant="critical" icon={ShieldOff} />
        <KpiCard label="Delayed Acks" value={kpis.delayed_acknowledgements} variant="warning" icon={Clock} />
        <KpiCard label="Repeated Unsafe" value={kpis.repeated_unsafe_conditions} variant="warning" icon={RefreshCw} />
        <KpiCard label="Pending Actions" value={kpis.pending_corrective_actions} variant="warning" icon={CheckSquare} />
      </div>

      {/* Charts Row 1 */}
      <div className="charts-grid">
        {/* Alarm Trend */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Alarm Trend — Last 30 Days</span>
          </div>
          {trends.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>
              No alarm data yet. Run data generation first.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="var(--color-border)" tickFormatter={d => d?.slice(5)} />
                <YAxis tick={{ fontSize: 10 }} stroke="var(--color-border)" />
                <Tooltip content={<CustomTooltip />} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
                <Area type="monotone" dataKey="CRITICAL" stackId="1" stroke={SEVERITY_COLORS.CRITICAL} fill={SEVERITY_COLORS.CRITICAL} fillOpacity={0.3} />
                <Area type="monotone" dataKey="HIGH" stackId="1" stroke={SEVERITY_COLORS.HIGH} fill={SEVERITY_COLORS.HIGH} fillOpacity={0.3} />
                <Area type="monotone" dataKey="MEDIUM" stackId="1" stroke={SEVERITY_COLORS.MEDIUM} fill={SEVERITY_COLORS.MEDIUM} fillOpacity={0.2} />
                <Area type="monotone" dataKey="LOW" stackId="1" stroke={SEVERITY_COLORS.LOW} fill={SEVERITY_COLORS.LOW} fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Severity Pie */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Severity Distribution</span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={severityPie} cx="50%" cy="50%" innerRadius={60} outerRadius={90} dataKey="value" paddingAngle={2}>
                {severityPie.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(val) => val.toLocaleString()} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Machines by Risk */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <span className="card-title">Top 10 Machines by Risk Score</span>
        </div>
        {riskScores.length === 0 ? (
          <div style={{ color: 'var(--color-text-muted)', padding: 20, textAlign: 'center' }}>No data yet</div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={riskScores} layout="vertical" margin={{ left: 40, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} stroke="var(--color-border)" />
              <YAxis type="category" dataKey="machine_id" tick={{ fontSize: 9 }} width={80}
                tickFormatter={(id) => id?.split('-').slice(-2).join('-')} stroke="var(--color-border)" />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="risk_score" fill="#2dd4bf" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Recent Critical Events */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Recent Critical Alarm Events</span>
        </div>
        {recentCritical.length === 0 ? (
          <div style={{ color: 'var(--color-text-muted)', padding: 20, textAlign: 'center' }}>
            No critical alarms yet. Generate data to populate this view.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Alarm Code</th>
                  <th>Machine</th>
                  <th>Severity</th>
                  <th>Ack Status</th>
                  <th>Timestamp</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentCritical.map(alarm => (
                  <tr key={alarm.id}>
                    <td><span className="mono">{alarm.alarm_event_code}</span></td>
                    <td><span className="mono" style={{ fontSize: 11 }}>{alarm.machine_id?.slice(0, 8)}…</span></td>
                    <td><SeverityBadge severity={alarm.severity} /></td>
                    <td><StatusBadge status={alarm.acknowledgement_status} /></td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>{formatTimestamp(alarm.alarm_timestamp)}</td>
                    <td><StatusBadge status={alarm.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
