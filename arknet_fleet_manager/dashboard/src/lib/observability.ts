import { createLogger, ConsoleTransport, BufferTransport, LogLevel } from './logger';
import { initializeErrorHandler } from './errors';

/**
 * Global logger configuration
 */
const isDevelopment = process.env.NODE_ENV === 'development';

// Create transports
const consoleTransport = new ConsoleTransport({
  useColors: true,
  useEmoji: true,
});

const bufferTransport = new BufferTransport(1000);

// Optionally add remote transport in production
// const remoteTransport = new RemoteTransport('https://logs.example.com/api/logs');

/**
 * Create the root logger
 */
export const rootLogger = createLogger('App', {
  minLevel: isDevelopment ? LogLevel.DEBUG : LogLevel.INFO,
  transports: [consoleTransport, bufferTransport],
  enabled: true,
});

/**
 * Initialize global error handler with the root logger
 */
export const errorHandler = initializeErrorHandler(rootLogger);

/**
 * Export buffer transport for log retrieval
 */
export { bufferTransport };

/**
 * Helper to get logs from buffer
 */
export function getBufferedLogs() {
  return bufferTransport.getEntries();
}

/**
 * Helper to clear buffered logs
 */
export function clearBufferedLogs() {
  bufferTransport.clear();
}

/**
 * Create a component logger
 */
export function createComponentLogger(componentName: string) {
  return rootLogger.child(componentName);
}

// Export everything from logger and errors (avoid re-exporting retry to prevent init cycle)
export * from './logger';
export * from './errors';
