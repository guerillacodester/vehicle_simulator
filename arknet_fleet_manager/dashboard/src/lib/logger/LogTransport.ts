import { LogEntry } from './LogEntry';

/**
 * Transport interface for log output destinations
 */
export interface ILogTransport {
  log(entry: LogEntry): void | Promise<void>;
  flush?(): void | Promise<void>;
}

/**
 * Console transport - outputs to browser console
 */
export class ConsoleTransport implements ILogTransport {
  private readonly useColors: boolean;
  private readonly useEmoji: boolean;

  constructor(options: { useColors?: boolean; useEmoji?: boolean } = {}) {
    this.useColors = options.useColors ?? true;
    this.useEmoji = options.useEmoji ?? true;
  }

  log(entry: LogEntry): void {
    const { level, message, component, action, metadata, error } = entry;
    
    const emoji = this.useEmoji ? this.getEmoji(level) : '';
    const prefix = `${emoji}[${component}${action ? `:${action}` : ''}]`;
    
    const consoleMethod = this.getConsoleMethod(level);
    const args: unknown[] = [prefix, message];
    
    if (metadata && Object.keys(metadata).length > 0) {
      args.push('\nMetadata:', metadata);
    }
    
    if (error) {
      args.push('\nError:', error);
      if (error.stack) {
        args.push('\nStack:', error.stack);
      }
    }
    
    if (this.useColors) {
      consoleMethod.apply(console, [
        `%c${args[0]}`,
        this.getStyle(level),
        ...args.slice(1)
      ]);
    } else {
      consoleMethod.apply(console, args);
    }
  }

  private getConsoleMethod(level: number): (...args: unknown[]) => void {
    if (level <= 2) return console.error;
    if (level === 3) return console.error;
    if (level === 4) return console.warn;
    if (level <= 6) return console.info;
    return console.debug;
  }

  private getStyle(level: number): string {
    const styles: Record<number, string> = {
      0: 'color: #ff0000; font-weight: bold; background: #ffcccc; padding: 2px 4px;',
      1: 'color: #ff3300; font-weight: bold; background: #ffe6e6; padding: 2px 4px;',
      2: 'color: #ff6600; font-weight: bold; background: #fff0e6; padding: 2px 4px;',
      3: 'color: #ff0000; font-weight: bold;',
      4: 'color: #ff9900; font-weight: bold;',
      5: 'color: #0066cc; font-weight: bold;',
      6: 'color: #0099ff;',
      7: 'color: #666666;',
      8: 'color: #999999;',
    };
    return styles[level] || styles[6];
  }

  private getEmoji(level: number): string {
    const emojis: Record<number, string> = {
      0: '🚨',
      1: '🔥',
      2: '💥',
      3: '❌',
      4: '⚠️',
      5: '📢',
      6: '📝',
      7: '🔍',
      8: '🔬',
    };
    return emojis[level] || '📝';
  }
}

/**
 * Buffer transport - stores logs in memory for later retrieval
 */
export class BufferTransport implements ILogTransport {
  private buffer: LogEntry[] = [];
  private readonly maxSize: number;

  constructor(maxSize: number = 1000) {
    this.maxSize = maxSize;
  }

  log(entry: LogEntry): void {
    this.buffer.push(entry);
    
    // Keep buffer size under control
    if (this.buffer.length > this.maxSize) {
      this.buffer = this.buffer.slice(-this.maxSize);
    }
  }

  getEntries(): readonly LogEntry[] {
    return [...this.buffer];
  }

  clear(): void {
    this.buffer = [];
  }

  flush(): void {
    this.buffer = [];
  }
}

/**
 * Remote transport - sends logs to a remote endpoint
 */
export class RemoteTransport implements ILogTransport {
  private readonly endpoint: string;
  private readonly batchSize: number;
  private readonly flushInterval: number;
  private buffer: LogEntry[] = [];
  private timer?: NodeJS.Timeout;

  constructor(
    endpoint: string,
    options: { batchSize?: number; flushInterval?: number } = {}
  ) {
    this.endpoint = endpoint;
    this.batchSize = options.batchSize ?? 10;
    this.flushInterval = options.flushInterval ?? 5000;
    
    this.startFlushTimer();
  }

  log(entry: LogEntry): void {
    this.buffer.push(entry);
    
    if (this.buffer.length >= this.batchSize) {
      this.flush();
    }
  }

  async flush(): Promise<void> {
    if (this.buffer.length === 0) return;

    const entries = [...this.buffer];
    this.buffer = [];

    try {
      await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: entries }),
      });
    } catch (error) {
      console.error('Failed to send logs to remote endpoint:', error);
      // Re-add entries to buffer for retry (optional)
      // this.buffer.unshift(...entries);
    }
  }

  private startFlushTimer(): void {
    this.timer = setInterval(() => {
      this.flush().catch(console.error);
    }, this.flushInterval);
  }

  destroy(): void {
    if (this.timer) {
      clearInterval(this.timer);
    }
    this.flush().catch(console.error);
  }
}

/**
 * LocalStorage transport - persists logs to browser storage
 */
export class LocalStorageTransport implements ILogTransport {
  private readonly key: string;
  private readonly maxEntries: number;

  constructor(key: string = 'app_logs', maxEntries: number = 500) {
    this.key = key;
    this.maxEntries = maxEntries;
  }

  log(entry: LogEntry): void {
    try {
      const existing = this.getEntries();
      existing.push(entry);
      
      // Keep only the latest entries
      const entries = existing.slice(-this.maxEntries);
      
      localStorage.setItem(this.key, JSON.stringify(entries));
    } catch (error) {
      console.error('Failed to write log to localStorage:', error);
    }
  }

  getEntries(): LogEntry[] {
    try {
      const data = localStorage.getItem(this.key);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  }

  clear(): void {
    localStorage.removeItem(this.key);
  }

  flush(): void {
    this.clear();
  }
}
