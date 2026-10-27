import React from 'react';
import { NavLink } from 'react-router-dom';
import { Sun, Moon,
  LayoutDashboard, Factory, Cpu, ShieldAlert, Zap, Bell, BellRing,
  Users, AlertTriangle, CheckSquare, Search, BarChart3,
  Database, ClipboardCheck, FileText, Activity, Shield, Download,
} from 'lucide-react';

const NAV_SECTIONS = [
  {
    label: 'Overview',
    items: [
      { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    ],
  },
  {
    label: 'Plant Operations',
    items: [
      { path: '/plants', icon: Factory, label: 'Plants' },
      { path: '/machines', icon: Cpu, label: 'Machines' },
      { path: '/safety-zones', icon: ShieldAlert, label: 'Safety Zones' },
      { path: '/interlocks', icon: Zap, label: 'Interlocks' },
    ],
  },
  {
    label: 'Alarm Management',
    items: [
      { path: '/alarm-definitions', icon: Bell, label: 'Alarm Definitions' },
      { path: '/alarms', icon: BellRing, label: 'Alarm Events' },
      { path: '/operator-shifts', icon: Users, label: 'Operator Shifts' },
    ],
  },
  {
    label: 'Safety & Incidents',
    items: [
      { path: '/incidents', icon: AlertTriangle, label: 'Incidents' },
      { path: '/corrective-actions', icon: CheckSquare, label: 'Corrective Actions' },
      { path: '/anomalies', icon: Search, label: 'Anomaly Detection' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { path: '/analytics', icon: BarChart3, label: 'Analytics' },
      { path: '/data-generator', icon: Database, label: 'Data Generator' },
      { path: '/validation', icon: ClipboardCheck, label: 'Validation' },
      { path: '/audit', icon: FileText, label: 'Audit Trail' },
      { path: '/exports', icon: Download, label: 'Exports' },
    ],
  },
];

export default function Sidebar({ theme, toggleTheme }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={18} color="var(--color-teal)" style={{ filter: 'drop-shadow(0 0 6px var(--color-teal))', animation: 'pulse 3s ease-in-out infinite' }} />
          <h1>SafePlant AI</h1>
        </div>
        <span>Industrial Safety Intelligence</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map(({ path, icon: Icon, label }) => (
              <NavLink
                key={path}
                to={path}
                end={path === '/'}
                className={({ isActive }) =>
                  `sidebar-item ${isActive ? 'active' : ''}`
                }
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div style={{
        padding: '12px 16px',
        borderTop: '1px solid var(--color-sidebar-border)',
        fontSize: 11,
        color: 'var(--color-text-muted)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span className="status-dot online" />
            API Connected
          </div>
          <button
            onClick={toggleTheme}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            style={{
              background: 'var(--color-bg-hover)',
              border: '1px solid var(--color-border)',
              borderRadius: 6,
              padding: '4px 6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: 'var(--color-text-secondary)',
            }}
          >
            {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
          </button>
        </div>
        <div>Seed: 20261022 | v1.0.0</div>
      </div>
    </aside>
  );
}
