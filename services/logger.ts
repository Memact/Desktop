
import { LogEvent } from '../types';
import { MAX_EVENTS, RETENTION_HOURS } from '../constants';

const STORAGE_KEY = 'memact_logs';

export const getLogs = (): LogEvent[] => {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
};

export const saveEvent = (event: LogEvent): void => {
  const logs = getLogs();
  
  // Rule: Only log on change
  const lastEvent = logs[logs.length - 1];
  if (lastEvent && lastEvent.process_name === event.process_name && lastEvent.window_title === event.window_title) {
    return;
  }

  const updatedLogs = [...logs, event];

  // Retention Rules: 48 hours OR 10,000 events
  const now = Date.now();
  const cutoff = now - RETENTION_HOURS * 60 * 60 * 1000;
  
  const prunedLogs = updatedLogs
    .filter(log => log.timestamp > cutoff)
    .slice(-MAX_EVENTS);

  localStorage.setItem(STORAGE_KEY, JSON.stringify(prunedLogs));
};

// For Simulation Purposes: Populate some historical data if empty
export const seedMockData = () => {
  const logs = getLogs();
  if (logs.length > 0) return;

  const now = Date.now();
  const mockEvents: LogEvent[] = [
    { timestamp: now - 300000, process_name: 'chrome.exe', window_title: 'Google Docs - Project Plan' },
    { timestamp: now - 250000, process_name: 'slack.exe', window_title: 'General - Memact' },
    { timestamp: now - 200000, process_name: 'chrome.exe', window_title: 'Stack Overflow' },
    { timestamp: now - 150000, process_name: 'code.exe', window_title: 'App.tsx - memact' },
    { timestamp: now - 50000, process_name: 'chrome.exe', window_title: 'New Tab' },
  ];

  localStorage.setItem(STORAGE_KEY, JSON.stringify(mockEvents));
};
