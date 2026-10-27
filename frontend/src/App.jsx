import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import Plants from './pages/Plants';
import Machines from './pages/Machines';
import MachineDetails from './pages/MachineDetails';
import SafetyZones from './pages/SafetyZones';
import Interlocks from './pages/Interlocks';
import AlarmDefinitions from './pages/AlarmDefinitions';
import Alarms from './pages/Alarms';
import AlarmDetails from './pages/AlarmDetails';
import OperatorShifts from './pages/OperatorShifts';
import Incidents from './pages/Incidents';
import IncidentDetails from './pages/IncidentDetails';
import CorrectiveActions from './pages/CorrectiveActions';
import Analytics from './pages/Analytics';
import Anomalies from './pages/Anomalies';
import DataGenerator from './pages/DataGenerator';
import Validation from './pages/Validation';
import AuditTrail from './pages/AuditTrail';
import Exports from './pages/Exports';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  return (
    <div className="app-layout">
      <Sidebar theme={theme} toggleTheme={toggleTheme} />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/plants" element={<Plants />} />
          <Route path="/machines" element={<Machines />} />
          <Route path="/machines/:id" element={<MachineDetails />} />
          <Route path="/safety-zones" element={<SafetyZones />} />
          <Route path="/interlocks" element={<Interlocks />} />
          <Route path="/alarm-definitions" element={<AlarmDefinitions />} />
          <Route path="/alarms" element={<Alarms />} />
          <Route path="/alarms/:id" element={<AlarmDetails />} />
          <Route path="/operator-shifts" element={<OperatorShifts />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/incidents/:id" element={<IncidentDetails />} />
          <Route path="/corrective-actions" element={<CorrectiveActions />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/data-generator" element={<DataGenerator />} />
          <Route path="/validation" element={<Validation />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="/exports" element={<Exports />} />
        </Routes>
      </main>
    </div>
  );
}
