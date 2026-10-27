import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const msg = error.response.data?.message || 'An error occurred';
      return Promise.reject(new Error(msg));
    }
    return Promise.reject(error);
  }
);

// System
export const getHealth = () => api.get('/health'.replace('/api/v1', ''));

// Dashboard
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getDashboardTrends = (days = 30) => api.get(`/dashboard/trends?days=${days}`);

// Plants
export const getPlants = (params = {}) => api.get('/plants', { params });
export const getPlant = (id) => api.get(`/plants/${id}`);

// Machines
export const getMachines = (params = {}) => api.get('/machines', { params });
export const getMachine = (id) => api.get(`/machines/${id}`);
export const getMachineTimeline = (id) => api.get(`/machines/${id}/timeline`);

// Safety Zones
export const getSafetyZones = (params = {}) => api.get('/safety-zones', { params });
export const getSafetyZone = (id) => api.get(`/safety-zones/${id}`);

// Interlocks
export const getInterlocks = (params = {}) => api.get('/interlocks', { params });
export const getInterlock = (id) => api.get(`/interlocks/${id}`);

// Alarm Definitions
export const getAlarmDefinitions = (params = {}) => api.get('/alarm-definitions', { params });

// Alarms
export const getAlarms = (params = {}) => api.get('/alarms', { params });
export const getAlarm = (id) => api.get(`/alarms/${id}`);
export const getAlarmTimeline = (id) => api.get(`/alarms/${id}/timeline`);
export const acknowledgeAlarm = (id, body) => api.post(`/alarms/${id}/acknowledge`, body);
export const getAlarmFloods = () => api.get('/alarms/floods');
export const getNuisanceClusters = () => api.get('/alarms/nuisance-clusters');

// Operator Shifts
export const getOperatorShifts = (params = {}) => api.get('/operator-shifts', { params });
export const getOperatorShift = (id) => api.get(`/operator-shifts/${id}`);

// Incidents
export const getIncidents = (params = {}) => api.get('/incidents', { params });
export const getIncident = (id) => api.get(`/incidents/${id}`);
export const getIncidentTraceability = (id) => api.get(`/incidents/${id}/traceability`);
export const transitionIncident = (id, body) => api.post(`/incidents/${id}/transitions`, body);

// Corrective Actions
export const getCorrectiveActions = (params = {}) => api.get('/corrective-actions', { params });
export const getCorrectiveAction = (id) => api.get(`/corrective-actions/${id}`);
export const createCorrectiveAction = (body) => api.post('/corrective-actions', body);
export const transitionCorrectiveAction = (id, body) => api.post(`/corrective-actions/${id}/transitions`, body);
export const verifyCorrectiveAction = (id, body) => api.post(`/corrective-actions/${id}/verify`, body);

// Analytics
export const getAlarmTrends = (days = 30) => api.get(`/analytics/alarm-trends?days=${days}`);
export const getSeverityDistribution = () => api.get('/analytics/severity');
export const getMachineRisk = (limit = 10) => api.get(`/analytics/machine-risk?limit=${limit}`);
export const getRepeatedConditions = () => api.get('/analytics/repeated-conditions');
export const getAckAnalytics = () => api.get('/analytics/acknowledgements');
export const getIncidentAnalytics = () => api.get('/analytics/incidents');
export const getActionAnalytics = () => api.get('/analytics/actions');
export const getShiftPerformance = () => api.get('/analytics/shift-performance');

// Anomalies
export const getAnomalies = (params = {}) => api.get('/anomalies', { params });
export const getAnomaly = (id) => api.get(`/anomalies/${id}`);
export const detectAnomalies = () => api.post('/anomalies/detect');
export const getEvaluationMetrics = () => api.get('/evaluation/metrics');
export const getConfusionMatrix = () => api.get('/evaluation/confusion-matrix');

// Generator
export const runGenerator = (body) => api.post('/generator/run', body);
export const getGeneratorRuns = (params = {}) => api.get('/generator/runs', { params });
export const getGeneratorRun = (id) => api.get(`/generator/runs/${id}`);

// Validation
export const runValidation = (body = {}) => api.post('/validation/run', body);
export const getValidationReports = (params = {}) => api.get('/validation/reports', { params });
export const getValidationReport = (id) => api.get(`/validation/reports/${id}`);

// Exports
export const exportAlarms = () => `${API_BASE}/exports/alarms`;
export const exportIncidents = () => `${API_BASE}/exports/incidents`;
export const exportAnomalies = () => `${API_BASE}/exports/anomalies`;
export const exportValidation = () => `${API_BASE}/exports/validation`;

// Audit
export const getAuditLogs = (params = {}) => api.get('/audit-logs', { params });

export default api;
