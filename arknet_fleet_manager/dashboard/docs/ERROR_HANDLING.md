# Error Handling and Retry Logic

## Overview

The dashboard implements a robust, production-ready error handling and retry system with the following features:

- **Centralized Error Handling**: All errors are normalized and tracked through `ErrorHandler`
- **Circuit Breaker Pattern**: Prevents excessive retry attempts when services are consistently failing
- **Exponential Backoff with Jitter**: Smart retry delays to avoid overwhelming services
- **Error Recovery Strategies**: Specific recovery actions for different error types
- **Comprehensive Metrics**: Track error rates, recovery success, and connection health
- **User-Friendly Feedback**: Clear error messages and recommended actions for users

## Architecture

### Core Components

1. **ErrorCodes** (`ErrorCodes.ts`)
   - Standardized error code enum
   - Consistent error identification across the application

2. **ErrorHandler** (`ErrorHandler.ts`)
   - Centralizes error logging and normalization
   - Converts all errors to `AppError` instances
   - Provides structured error context

3. **RetryStrategy** (`RetryStrategy.ts`)
   - Configurable exponential backoff
   - Circuit breaker implementation
   - Retry attempt tracking

4. **ErrorRecovery** (`ErrorRecovery.ts`)
   - Recovery action determination per error type
   - Transient vs. permanent error classification
   - User action requirement detection

5. **TelemetryDataProvider** (`TelemetryDataProvider.ts`)
   - Integrates all error handling components
   - Tracks error metrics
   - Provides diagnostic information

## Usage

### Basic Error Handling

```typescript
import { ErrorHandler, ErrorCodes } from '@/lib/errors';

try {
  // Some operation
} catch (error) {
  const appError = ErrorHandler.handle({
    code: ErrorCodes.NETWORK_ERROR,
    message: 'Failed to connect',
    details: { error },
  });
  
  console.error('Error occurred:', appError);
}
```

### Configuring Retry Strategy

```typescript
import { RetryStrategy } from '@/lib/errors';

const retryStrategy = new RetryStrategy({
  maxRetries: -1,                   // -1 for infinite retries
  initialDelay: 1000,                // Start with 1 second
  maxDelay: 30000,                   // Cap at 30 seconds
  backoffMultiplier: 2,              // Double delay each retry
  jitterFactor: 0.1,                 // Add 10% randomness
  circuitBreakerThreshold: 5,        // Open circuit after 5 failures
  circuitBreakerTimeout: 60000,      // Try again after 60 seconds
});

// Check if we can retry
if (retryStrategy.canRetry()) {
  const delay = retryStrategy.getNextDelay();
  setTimeout(() => attemptConnection(), delay);
  retryStrategy.recordAttempt();
}

// Record outcome
if (success) {
  retryStrategy.recordSuccess();
} else {
  retryStrategy.recordFailure();
}
```

### Using Error Recovery

```typescript
import { ErrorRecovery } from '@/lib/errors';

const error = new AppError('Connection failed', ErrorCodes.NETWORK_ERROR);

// Get recovery action
const recovery = ErrorRecovery.getRecoveryAction(error);
console.log('Recovery type:', recovery.type);
console.log('Can auto-recover:', recovery.canAutoRecover);
console.log('Recommended delay:', recovery.delay);

// Check error characteristics
const isTransient = ErrorRecovery.isTransientError(error);
const needsUser = ErrorRecovery.requiresUserAction(error);

// Get user-facing messages
const userMessage = ErrorRecovery.getUserMessage(error);
const action = ErrorRecovery.getRecommendedAction(error);
```

### Accessing Diagnostics

```typescript
import { useTelemetry } from '@/core/telemetry/useTelemetry';

function DiagnosticsPanel() {
  const { diagnostics } = useTelemetry();
  
  return (
    <div>
      <h3>Connection Status</h3>
      <p>State: {diagnostics.state}</p>
      <p>Type: {diagnostics.connectionType}</p>
      
      <h3>Retry Statistics</h3>
      <p>Circuit State: {diagnostics.retryStats.circuitState}</p>
      <p>Attempts: {diagnostics.retryStats.attempts}</p>
      <p>Consecutive Failures: {diagnostics.retryStats.consecutiveFailures}</p>
      
      <h3>Error Metrics</h3>
      <p>Total Errors: {diagnostics.errorMetrics.totalErrors}</p>
      <p>Recovery Rate: {diagnostics.errorMetrics.recoveryRate}</p>
      <p>Successful Recoveries: {diagnostics.errorMetrics.successfulRecoveries}</p>
    </div>
  );
}
```

## Error Types and Recovery Actions

### Network Errors (`NETWORK_ERROR`)
- **Recovery**: Automatic retry with exponential backoff
- **User Action**: None required
- **Typical Causes**: Connection loss, timeout, DNS failure

### Authentication Errors

#### Token Expired (`TOKEN_EXPIRED`)
- **Recovery**: Automatic token refresh
- **User Action**: None required (if refresh token available)
- **Typical Causes**: Session timeout

#### Auth Failed (`AUTH_ERROR`)
- **Recovery**: User must re-authenticate
- **User Action**: Login required
- **Typical Causes**: Invalid credentials, refresh token expired

### Data Errors

#### Parse Error (`DATA_PARSE_ERROR`)
- **Recovery**: Log and continue (don't disconnect)
- **User Action**: None required
- **Typical Causes**: Malformed JSON, protocol mismatch

#### Validation Error (`DATA_VALIDATION_ERROR`)
- **Recovery**: Retry with delay
- **User Action**: None required
- **Typical Causes**: Invalid data format, missing fields

### Server Errors (`SERVER_ERROR`)
- **Recovery**: Try fallback connection (WebSocket → SSE)
- **User Action**: None required
- **Typical Causes**: Internal server error, service unavailable

### Rate Limiting (`RATE_LIMIT_ERROR`)
- **Recovery**: Longer backoff (10+ seconds)
- **User Action**: None required
- **Typical Causes**: Too many requests

## Circuit Breaker States

### CLOSED (Normal Operation)
- All connection attempts are allowed
- Errors are tracked
- Transitions to OPEN after threshold failures

### OPEN (Service Down)
- Connection attempts are blocked
- Prevents overwhelming failed services
- Transitions to HALF_OPEN after timeout

### HALF_OPEN (Testing Recovery)
- Allow one connection attempt
- If successful: transition to CLOSED
- If failed: transition back to OPEN

## Best Practices

### 1. Always Use Error Codes
```typescript
// Good
const error = ErrorHandler.handle({
  code: ErrorCodes.NETWORK_ERROR,
  message: 'Connection failed',
});

// Bad
throw new Error('Connection failed');
```

### 2. Provide Context in Error Details
```typescript
const error = ErrorHandler.handle({
  code: ErrorCodes.DATA_PARSE_ERROR,
  message: 'Failed to parse message',
  details: {
    rawData: event.data,
    parserError: error,
    timestamp: Date.now(),
  },
});
```

### 3. Check Recovery Actions Before Handling
```typescript
const recovery = ErrorRecovery.getRecoveryAction(error);

if (recovery.canAutoRecover) {
  // Handle automatically
  setTimeout(() => retry(), recovery.delay);
} else {
  // Show user intervention UI
  showLoginPrompt();
}
```

### 4. Monitor Error Metrics
```typescript
const diagnostics = telemetryProvider.getDiagnostics();

// Alert if error rate is high
if (diagnostics.errorMetrics.totalErrors > threshold) {
  sendAlert('High error rate detected');
}

// Alert if recovery rate is low
const recoveryRate = parseFloat(diagnostics.errorMetrics.recoveryRate);
if (recoveryRate < 50) {
  sendAlert('Low recovery success rate');
}
```

### 5. Use Circuit Breaker Stats for Health Checks
```typescript
const stats = diagnostics.retryStats;

if (stats.circuitState === 'open') {
  // Service is considered down
  showServiceDownBanner();
} else if (stats.consecutiveFailures > 3) {
  // Service is struggling
  showDegradedServiceWarning();
}
```

## Troubleshooting

### High Error Rates
1. Check `errorMetrics.errorsByType` to identify most common errors
2. Review `retryStats.consecutiveFailures` for persistent issues
3. Examine `lastError` for recent error details

### Circuit Breaker Constantly Open
1. Verify backend service health
2. Check network connectivity
3. Review `circuitBreakerThreshold` configuration
4. Increase `circuitBreakerTimeout` if service needs more recovery time

### Poor Recovery Rate
1. Check if errors are transient vs. permanent
2. Verify token refresh logic is working
3. Review fallback mechanisms (WebSocket → SSE)
4. Check if `maxRetries` is too low

### Connection Never Recovers
1. Verify `maxRetries` is set to -1 (infinite)
2. Check if circuit breaker timeout is appropriate
3. Ensure backend service is actually available
4. Review error logs for auth or permission issues

## Testing

Run error handling tests:
```bash
npm test -- RetryStrategy.test.ts
npm test -- ErrorRecovery.test.ts
```

Test circuit breaker behavior:
```bash
npm test -- --testNamePattern="Circuit Breaker"
```

## Metrics and Monitoring

The error handling system tracks:

- **Total Errors**: Cumulative error count
- **Errors by Type**: Breakdown of error codes
- **Recovery Attempts**: How many times recovery was attempted
- **Successful Recoveries**: How many recoveries succeeded
- **Recovery Rate**: Percentage of successful recoveries
- **Circuit State**: Current circuit breaker state
- **Consecutive Failures**: Failures since last success
- **Last Error**: Most recent error with timestamp

Use these metrics for:
- Real-time health monitoring
- Alerting and notifications
- Performance analysis
- Capacity planning

## Future Enhancements

Potential improvements:
- Remote error reporting service integration
- Error correlation and pattern detection
- Adaptive retry strategies based on error patterns
- Per-error-type circuit breakers
- User notification preferences
- Error replay/reproduction tools
