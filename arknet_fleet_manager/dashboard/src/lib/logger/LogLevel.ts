/**
 * Log Levels following RFC 5424 (Syslog Protocol)
 */
export enum LogLevel {
  EMERGENCY = 0, // System is unusable
  ALERT = 1,     // Action must be taken immediately
  CRITICAL = 2,  // Critical conditions
  ERROR = 3,     // Error conditions
  WARNING = 4,   // Warning conditions
  NOTICE = 5,    // Normal but significant condition
  INFO = 6,      // Informational messages
  DEBUG = 7,     // Debug-level messages
  TRACE = 8      // Trace-level messages (most verbose)
}

export const LogLevelNames: Record<LogLevel, string> = {
  [LogLevel.EMERGENCY]: 'EMERGENCY',
  [LogLevel.ALERT]: 'ALERT',
  [LogLevel.CRITICAL]: 'CRITICAL',
  [LogLevel.ERROR]: 'ERROR',
  [LogLevel.WARNING]: 'WARNING',
  [LogLevel.NOTICE]: 'NOTICE',
  [LogLevel.INFO]: 'INFO',
  [LogLevel.DEBUG]: 'DEBUG',
  [LogLevel.TRACE]: 'TRACE',
};
