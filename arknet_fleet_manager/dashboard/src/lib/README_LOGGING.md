# Production-Grade Logging & Error Handling System

A robust, enterprise-grade logging and error handling system following SOLID principles and industry best practices.

## 🎯 Features

- **Structured Logging**: RFC 5424 compliant log levels with rich metadata
- **Compartmentalized Errors**: Error categories for different failure domains
- **Multiple Transports**: Console, Buffer, LocalStorage, and Remote logging
- **Error Boundaries**: React error boundaries with automatic error capture
- **Retry Logic**: Configurable retry mechanisms with exponential backoff
- **Performance Tracking**: Built-in timing and metrics collection
- **Correlation IDs**: Request tracing across operations
- **Type-Safe**: Full TypeScript support with strict typing

## 📁 Architecture

```
lib/
├── logger/
│   ├── LogLevel.ts         # Log level definitions (RFC 5424)
│   ├── LogEntry.ts         # Structured log entry interface
│   ├── LogTransport.ts     # Transport implementations
│   ├── Logger.ts           # Core logger implementation
│   └── index.ts            # Logger exports
├── errors/
│   ├── AppError.ts         # Base error classes
│   ├── ErrorHandler.ts     # Centralized error handler
│   └── index.ts            # Error exports
├── utils/
│   └── retry.ts            # Retry utilities
├── observability.ts        # Main entry point
└── USAGE_EXAMPLES.ts       # Usage documentation
```

## 🚀 Quick Start

### 1. Initialize the System

The system is auto-initialized in `observability.ts`, but you can customize it:

```typescript
import { rootLogger, errorHandler } from '@/lib/observability';

// The logger and error handler are ready to use!
```

### 2. Create a Component Logger

```typescript
import { createComponentLogger } from '@/lib/observability';

const logger = createComponentLogger('MyComponent');

logger.info('Component initialized', {
  action: 'init',
  metadata: { version: '1.0.0' }
});
```

### 3. Handle Errors

```typescript
import { NetworkError, handleError } from '@/lib/observability';

try {
  const response = await fetch('/api/data');
  if (!response.ok) {
    throw new NetworkError('Failed to fetch data', {
      statusCode: response.status,
      url: response.url
    });
  }
} catch (error) {
  handleError(error, {
    component: 'DataService',
    action: 'fetchData'
  });
}
```

## 📊 Log Levels

Following RFC 5424 (Syslog Protocol):

| Level | Name | Usage |
|-------|------|-------|
| 0 | EMERGENCY | System is unusable |
| 1 | ALERT | Action must be taken immediately |
| 2 | CRITICAL | Critical conditions |
| 3 | ERROR | Error conditions |
| 4 | WARNING | Warning conditions |
| 5 | NOTICE | Normal but significant |
| 6 | INFO | Informational messages |
| 7 | DEBUG | Debug-level messages |
| 8 | TRACE | Trace-level (most verbose) |

## 🎭 Error Categories

Errors are compartmentalized by category:

- **NETWORK**: Network/API errors
- **VALIDATION**: Input validation errors
- **AUTHENTICATION**: Authentication errors
- **AUTHORIZATION**: Permission errors
- **NOT_FOUND**: Resource not found
- **CONFLICT**: Resource conflict
- **BUSINESS_LOGIC**: Business rule violations
- **SYSTEM**: System/infrastructure errors
- **EXTERNAL**: Third-party service errors
- **UNKNOWN**: Unknown errors

## 🔄 Transports

### Console Transport
Outputs colorful, emoji-enhanced logs to browser console:

```typescript
import { ConsoleTransport } from '@/lib/observability';

const transport = new ConsoleTransport({
  useColors: true,
  useEmoji: true
});
```

### Buffer Transport
Stores logs in memory for later retrieval:

```typescript
import { BufferTransport } from '@/lib/observability';

const transport = new BufferTransport(1000); // max 1000 entries
const logs = transport.getEntries();
```

### LocalStorage Transport
Persists logs to browser storage:

```typescript
import { LocalStorageTransport } from '@/lib/observability';

const transport = new LocalStorageTransport('app_logs', 500);
```

### Remote Transport
Sends logs to a remote endpoint:

```typescript
import { RemoteTransport } from '@/lib/observability';

const transport = new RemoteTransport('https://logs.example.com/api/logs', {
  batchSize: 10,
  flushInterval: 5000
});
```

## 🔍 Advanced Features

### Performance Timing

```typescript
const result = await logger.timed('Complex operation', async () => {
  // Your operation here
  return await processData();
});
// Automatically logs duration
```

### Correlation IDs

```typescript
logger.setCorrelationId('req-123');
logger.info('Processing started');
logger.info('Processing completed');
logger.clearCorrelationId();
```

### Child Loggers

```typescript
const parentLogger = createComponentLogger('ServiceManager');
const socketLogger = parentLogger.child('Socket');
const apiLogger = parentLogger.child('API');

socketLogger.info('Connected'); // [ServiceManager:Socket] Connected
apiLogger.debug('Request sent'); // [ServiceManager:API] Request sent
```

### Retry Logic

```typescript
import { retry, isRetryableError } from '@/lib/observability';

const result = await retry(
  async () => await fetch('/api/data'),
  {
    maxAttempts: 3,
    delay: 1000,
    backoff: 'exponential',
    shouldRetry: isRetryableError
  }
);
```

## ⚛️ React Integration

### Error Boundary

```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      component="App"
      fallback={<ErrorFallback />}
      onError={(error, errorInfo) => {
        // Custom error handling
      }}
    >
      <YourApp />
    </ErrorBoundary>
  );
}
```

### HOC Wrapper

```tsx
import { withErrorBoundary } from '@/components/ErrorBoundary';

const SafeComponent = withErrorBoundary(MyComponent, {
  component: 'MyComponent'
});
```

## 📤 Exporting Logs

```typescript
import { getBufferedLogs } from '@/lib/observability';

function exportLogs() {
  const logs = getBufferedLogs();
  const blob = new Blob([JSON.stringify(logs, null, 2)], { 
    type: 'application/json' 
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `logs-${new Date().toISOString()}.json`;
  a.click();
}
```

## 🛠️ Configuration

### Development vs Production

```typescript
// In observability.ts
const isDevelopment = process.env.NODE_ENV === 'development';

const logger = createLogger('App', {
  minLevel: isDevelopment ? LogLevel.DEBUG : LogLevel.INFO,
  transports: [/* ... */],
  enabled: true
});
```

### Custom Transport

```typescript
import { ILogTransport, LogEntry } from '@/lib/observability';

class CustomTransport implements ILogTransport {
  log(entry: LogEntry): void {
    // Your custom logging logic
  }
}

logger.addTransport(new CustomTransport());
```

## 📝 Best Practices

1. **Create component-specific loggers**: Don't use the root logger directly
   ```typescript
   const logger = createComponentLogger('MyComponent');
   ```

2. **Use appropriate log levels**: Don't log everything as ERROR
   ```typescript
   logger.debug('Detailed debug info');
   logger.info('Normal operation');
   logger.warn('Something unusual');
   logger.error('Actual error', error);
   ```

3. **Include context in metadata**:
   ```typescript
   logger.error('Operation failed', error, {
     action: 'saveData',
     metadata: { userId, dataId }
   });
   ```

4. **Use structured errors**:
   ```typescript
   throw new ValidationError('Invalid input', {
     field: 'email',
     value: userInput
   });
   ```

5. **Wrap error-prone operations with retry**:
   ```typescript
   const data = await retry(() => fetchData(), {
     maxAttempts: 3,
     shouldRetry: isRetryableError
   });
   ```

6. **Wrap UI components with error boundaries**:
   ```tsx
   <ErrorBoundary component="Dashboard">
     <Dashboard />
   </ErrorBoundary>
   ```

## 🔒 Production Considerations

1. **Log Levels**: Set to INFO or higher in production
2. **PII Data**: Never log sensitive user data
3. **Rate Limiting**: Use remote transport with batching
4. **Storage Limits**: Set appropriate buffer sizes
5. **Error Reporting**: Integrate with services like Sentry
6. **Monitoring**: Set up alerts for CRITICAL/ERROR levels

## 📚 Examples

See [USAGE_EXAMPLES.ts](./USAGE_EXAMPLES.ts) for comprehensive examples.

## 🤝 Contributing

When adding new error types or log transports:

1. Extend the base classes (`AppError`, `ILogTransport`)
2. Add appropriate error categories if needed
3. Document usage in USAGE_EXAMPLES.ts
4. Write unit tests

## 📄 License

Part of the ArkNet Fleet Management System.
