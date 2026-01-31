
export interface LogEvent {
  timestamp: number;
  process_name: string;
  window_title: string;
}

export interface Session {
  startTime: number;
  endTime: number;
  events: LogEvent[];
}

export enum AppState {
  IDLE = 'IDLE',
  SUBMITTED = 'SUBMITTED',
  NO_ACTIVITY = 'NO_ACTIVITY'
}

export interface ReconstructedActivity {
  text: string;
  timestamp: number;
}
