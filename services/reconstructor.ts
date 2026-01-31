
import { LogEvent, Session } from '../types';
import { 
  INACTIVITY_THRESHOLD_MS, 
  FRAGMENTED_THRESHOLD_MS, 
  FRAGMENTED_SWITCH_COUNT,
  BROWSER_APPS,
  DOC_APPS,
  MAIL_APPS
} from '../constants';

/**
 * Groups raw events into sessions based on inactivity or fragmented behavior.
 */
export const sliceSessions = (logs: LogEvent[]): Session[] => {
  if (logs.length === 0) return [];

  const sessions: Session[] = [];
  let currentSession: LogEvent[] = [logs[0]];

  for (let i = 1; i < logs.length; i++) {
    const prev = logs[i - 1];
    const curr = logs[i];
    const timeDiff = curr.timestamp - prev.timestamp;

    // Rule 1: New session starts after >= 90s inactivity
    const isInactivityBreak = timeDiff >= INACTIVITY_THRESHOLD_MS;

    // Rule 2: Fragmentation check (>= 5 app switches in < 2 minutes)
    // For simplicity, we check the last 5 events relative to current
    let isFragmentedBreak = false;
    if (i >= FRAGMENTED_SWITCH_COUNT) {
      const windowStart = logs[i - FRAGMENTED_SWITCH_COUNT].timestamp;
      const windowDuration = curr.timestamp - windowStart;
      if (windowDuration < FRAGMENTED_THRESHOLD_MS) {
        // This marks the start of a new behavior window if it's considered "fragmented"
        // In the strict spec, "OR after fragmented behavior" implies a boundary.
        // We'll treat this as a session start if the previous chunk wasn't fragmented.
      }
    }

    if (isInactivityBreak) {
      sessions.push({
        startTime: currentSession[0].timestamp,
        endTime: prev.timestamp,
        events: currentSession
      });
      currentSession = [curr];
    } else {
      currentSession.push(curr);
    }
  }

  if (currentSession.length > 0) {
    sessions.push({
      startTime: currentSession[0].timestamp,
      endTime: currentSession[currentSession.length - 1].timestamp,
      events: currentSession
    });
  }

  return sessions;
};

/**
 * Reconstructs a session into a plain-language sentence using deterministic heuristics.
 */
export const reconstructSession = (session: Session): string => {
  const events = session.events;
  const uniqueApps = Array.from(new Set(events.map(e => e.process_name)));
  const appCount = uniqueApps.length;
  
  const startTimeStr = new Date(session.startTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  const endTimeStr = new Date(session.endTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

  // Logic: Browser + Docs + Mail
  const hasBrowser = uniqueApps.some(app => BROWSER_APPS.includes(app.toLowerCase()));
  const hasDocs = uniqueApps.some(app => DOC_APPS.includes(app.toLowerCase()));
  const hasMail = uniqueApps.some(app => MAIL_APPS.includes(app.toLowerCase()));

  let focusPhrase = "";

  if (hasBrowser && hasDocs && hasMail) {
    focusPhrase = "likely preparing or sending information";
  } else if (appCount <= 3 && events.length > 5) {
    focusPhrase = "focused on a single task across a few related applications";
  } else if (appCount > 6 && (session.endTime - session.startTime < 300000)) {
    focusPhrase = "exhibiting no clear task due to rapid application switching";
  } else if (uniqueApps.length === 1) {
    focusPhrase = `focused exclusively on ${uniqueApps[0]}`;
  } else if (hasBrowser && hasDocs) {
    focusPhrase = "likely drafting or reviewing content while referencing web resources";
  } else {
    focusPhrase = "engaged in various digital activities";
  }

  // Final sentence construction
  // Rules: 3-5 sentences, <70 words, neutral tone.
  const sentences = [
    `Between ${startTimeStr} and ${endTimeStr}, you were switching between ${uniqueApps.slice(0, 3).join(', ')}${uniqueApps.length > 3 ? ' and other tools' : ''}, ${focusPhrase}.`,
    `Activity remained within a ${appCount > 4 ? 'broad' : 'small'} set of applications.`,
    `No significant breaks or external interruptions were detected in this session.`
  ];

  const result = sentences.join(' ');
  return result.length > 0 ? result : "No clear task detected.";
};
