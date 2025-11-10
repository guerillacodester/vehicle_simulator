import { LogLevel } from './LogLevel';
import { LogEntry, createLogEntry, createErrorMetadata } from './LogEntry';
import { ILogTransport } from './LogTransport';

/**
 * Logger configuration
 */
export interface LoggerConfig {
  component: string;
  minLevel?: LogLevel;
  transports?: ILogTransport[];
  enabled?: boolean;
  includeTimestamp?: boolean;
}

/**
 * Production-grade logger with structured logging
 */
export class Logger {
  private readonly component: string;
  private minLevel: LogLevel;
  private transports: ILogTransport[];
  private enabled: boolean;
  private correlationId?: string;

  constructor(config: LoggerConfig) {
    this.component = config.component;
    this.minLevel = config.minLevel ?? LogLevel.INFO;
    this.transports = config.transports ?? [];
    this.enabled = config.enabled ?? true;
  }

  /**
   * Set correlation ID for request tracing
   */
  setCorrelationId(id: string): void {
    this.correlationId = id;
  }

  /**
   * Clear correlation ID
   */
  clearCorrelationId(): void {
    this.correlationId = undefined;
  }

  /**
   * Set minimum log level
   */
  setMinLevel(level: LogLevel): void {
    this.minLevel = level;
  }

  /**
   * Enable/disable logging
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Add a transport
   */
  addTransport(transport: ILogTransport): void {
    this.transports.push(transport);
  }

  /**
   * Emergency: System is unusable
   */
  emergency(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.EMERGENCY, message, options);
  }

  /**
   * Alert: Action must be taken immediately
   */
  alert(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.ALERT, message, options);
  }

  /**
   * Critical: Critical conditions
   */
  critical(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.CRITICAL, message, options);
  }

  /**
   * Error: Error conditions
   */
  error(message: string, error?: Error | unknown, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message' | 'error'>>): void {
    const errorMetadata = error ? createErrorMetadata(error) : undefined;
    this.log(LogLevel.ERROR, message, { ...options, error: errorMetadata });
  }

  /**
   * Warning: Warning conditions
   */
  warn(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.WARNING, message, options);
  }

  /**
   * Notice: Normal but significant condition
   */
  notice(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.NOTICE, message, options);
  }

  /**
   * Info: Informational messages
   */
  info(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.INFO, message, options);
  }

  /**
   * Debug: Debug-level messages
   */
  debug(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.DEBUG, message, options);
  }

  /**
   * Trace: Most verbose logging
   */
  trace(message: string, options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>): void {
    this.log(LogLevel.TRACE, message, options);
  }

  /**
   * Log a message with performance timing
   */
  async timed<T>(
    message: string,
    fn: () => T | Promise<T>,
    level: LogLevel = LogLevel.DEBUG
  ): Promise<T> {
    const start = performance.now();
    
    this.log(level, `${message} - Started`);
    
    try {
      const result = await fn();
      const duration = performance.now() - start;
      
      this.log(level, `${message} - Completed`, {
        metrics: { duration: Math.round(duration) }
      });
      
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      
      this.error(`${message} - Failed`, error, {
        metrics: { duration: Math.round(duration) }
      });
      
      throw error;
    }
  }

  /**
   * Create a child logger with the same configuration
   */
  child(component: string): Logger {
    return new Logger({
      component: `${this.component}:${component}`,
      minLevel: this.minLevel,
      transports: this.transports,
      enabled: this.enabled,
    });
  }

  /**
   * Core logging method
   */
  private log(
    level: LogLevel,
    message: string,
    options?: Partial<Omit<LogEntry, 'timestamp' | 'level' | 'component' | 'message'>>
  ): void {
    if (!this.enabled || level > this.minLevel) {
      return;
    }

    const entry = createLogEntry(level, this.component, message, {
      ...options,
      correlationId: options?.correlationId ?? this.correlationId,
    });

    // Send to all transports
    for (const transport of this.transports) {
      try {
        transport.log(entry);
      } catch (error) {
        // Defensive logging: transports must not be allowed to crash the
        // application. Some environments' console methods can throw when
        // passed exotic objects; wrap console calls in try/catch and
        // fall back to a minimal string-based message.
        try {
          // Prefer structured console.error when available
          console.error('Transport error:', error);
        } catch {
          try {
            // Fallback: stringified form
            const eStr = (() => {
              try { return typeof error === 'string' ? error : JSON.stringify(error); } catch { return String(error); }
            })();
            console.log(`Transport error: ${eStr}`);
          } catch {
            // Last resort: swallow — cannot allow logging to break app flow
          }
        }
      }
    }
  }
}

/**
 * Create a logger instance
 */
export function createLogger(component: string, config?: Partial<LoggerConfig>): Logger {
  return new Logger({
    component,
    ...config,
  });
}
