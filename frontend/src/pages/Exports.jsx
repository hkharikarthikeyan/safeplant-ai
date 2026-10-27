import React, { useState } from 'react';
import { Download, FileText, AlertTriangle, Bell, ClipboardCheck } from 'lucide-react';

const BASE = 'http://localhost:5000/api/v1';

const EXPORTS = [
  {
    key: 'alarms',
    label: 'Alarm Events',
    description: 'All alarm events with severity, status, timestamps and fingerprints',
    icon: Bell,
    url: `${BASE}/exports/alarms`,
    filename: 'alarms.csv',
    type: 'CSV',
    color: '#ef4444',
  },
  {
    key: 'incidents',
    label: 'Incidents',
    description: 'All safety incidents with root cause, status and engineer assignments',
    icon: AlertTriangle,
    url: `${BASE}/exports/incidents`,
    filename: 'incidents.csv',
    type: 'CSV',
    color: '#f59e0b',
  },
  {
    key: 'anomalies',
    label: 'Detected Anomalies',
    description: 'All detected anomalies from the anomaly detection engine',
    icon: FileText,
    url: `${BASE}/exports/anomalies`,
    filename: 'anomalies.csv',
    type: 'CSV',
    color: '#2dd4bf',
  },
  {
    key: 'validation',
    label: 'Validation Report',
    description: 'Latest validation run results with all 22 integrity check outcomes',
    icon: ClipboardCheck,
    url: `${BASE}/exports/validation`,
    filename: 'validation.json',
    type: 'JSON',
    color: '#22c55e',
  },
];

export default function Exports() {
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});

  const handleDownload = async (exp) => {
    setLoading(l => ({ ...l, [exp.key]: true }));
    setErrors(e => ({ ...e, [exp.key]: null }));
    try {
      const res = await fetch(exp.url);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = exp.filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setErrors(e => ({ ...e, [exp.key]: err.message }));
    } finally {
      setLoading(l => ({ ...l, [exp.key]: false }));
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 600 }}>Exports</h2>
        <p style={{ margin: '4px 0 0', color: 'var(--color-text-muted)', fontSize: 13 }}>
          Download data as CSV or JSON files
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 16 }}>
        {EXPORTS.map((exp) => {
          const Icon = exp.icon;
          return (
            <div key={exp.key} className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 8,
                  background: `${exp.color}22`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <Icon size={18} color={exp.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{exp.label}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: '2px 6px',
                      borderRadius: 4, background: `${exp.color}22`, color: exp.color,
                    }}>{exp.type}</span>
                  </div>
                  <p style={{ margin: '0 0 14px', fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
                    {exp.description}
                  </p>
                  {errors[exp.key] && (
                    <p style={{ margin: '0 0 10px', fontSize: 12, color: 'var(--color-red)' }}>
                      {errors[exp.key]}
                    </p>
                  )}
                  <button
                    onClick={() => handleDownload(exp)}
                    disabled={loading[exp.key]}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6,
                      padding: '7px 14px', borderRadius: 6, border: 'none',
                      background: exp.color, color: '#fff', fontWeight: 600,
                      fontSize: 12, cursor: loading[exp.key] ? 'not-allowed' : 'pointer',
                      opacity: loading[exp.key] ? 0.6 : 1,
                    }}
                  >
                    <Download size={13} />
                    {loading[exp.key] ? 'Downloading...' : `Download ${exp.type}`}
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
