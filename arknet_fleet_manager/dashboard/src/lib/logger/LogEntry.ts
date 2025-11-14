import { LogLevel } from './LogLevel';

/**
 * Structured log entry following best practices
 */
export interface LogEntry {
  // Core fields
  timestamp: string;
  level: LogLevel;
  message: string;
  
  // Context fields
  component: string;      // Component/module name (e.g., 'ServiceManager', 'SocketManager')
  action?: string;        // Action being performed (e.g., 'connect', 'startService')
  
  // Additional context
  metadata?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
    code?: string;
  };
  
  // Request context (for API calls)
  request?: {
    method?: string;
    url?: string;
    params?: Record<string, unknown>;
  };
  
  // User context
  user?: {
    id?: string;
    session?: string;
  };
  
  // Performance metrics
  metrics?: {
    duration?: number;    // Duration in milliseconds
    memory?: number;      // Memory usage in bytes
  };
  
  // Correlation
  correlationId?: string; // For tracing across multiple operations
  traceId?: string;       // Distributed tracing ID
}

/**
 * Helper to create a log entry
 */
export function createLogEntry(
  level: LogLevel,
  component: string,
  message: string,
  options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>
): LogEntry {
  return {
    timestamp: new Date().toISOString(),
    level,
    component,
    message,
    ...options,
  };
}

/**
 * Helper to create error metadata
 */
export function createErrorMetadata(error: Error | unknown): LogEntry['error'] {
  if (error instanceof Error) {
    return {
      name: error.name,
      message: error.message,
      stack: error.stack,
      code: (error as Error & { code?: string }).code,
    };
  }
  
  return {
    name: 'UnknownError',
    message: String(error),
  };
}
