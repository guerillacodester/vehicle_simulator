/**
 * Example usage documentation for the logging and error handling system
 * This file is for documentation purposes only
 */

/* eslint-disable @typescript-eslint/no-unused-vars */

import { 
  createComponentLogger, 
  NetworkError,
  ValidationError,
  ConnectionError,
  handleError,
  retry,
  isRetryableError
} from '@/lib/observability';

// ============================================================================
// CREATING LOGGERS
// ============================================================================

// Create a logger for your component
const serviceLogger = createComponentLogger('ServiceManager');

// ============================================================================
// BASIC LOGGING
// ============================================================================

// Different log levels
serviceLogger.info('Service started successfully', {
  action: 'start',
  metadata: { serviceName: 'vehicle_simulator', port: 8000 }
});

serviceLogger.debug('Processing request', {
  action: 'process',
  metadata: { requestId: '123', userId: 'user_456' }
});

serviceLogger.warn('High memory usage detected', {
  metadata: { memory: 1024 * 1024 * 512 }
});

serviceLogger.error('Failed to start service', new Error('Port already in use'), {
  action: 'start',
  metadata: { serviceName: 'gpscentcom', port: 5000 }
});

// ============================================================================
// PERFORMANCE TIMING
// ============================================================================

async function loadData() {
  return await serviceLogger.timed('Load service data', async () => {
    // Your async operation
    const response = await fetch('/api/services');
    return response.json();
  });
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

// Creating structured errors
function validateInput(input: string) {
  if (!input) {
    throw new ValidationError('Input is required', {
      field: 'serviceName',
      value: input,
      code: 'REQUIRED_FIELD'
    });
  }
}

// Network errors
async function fetchService(name: string) {
  try {
    const response = await fetch(`/api/services/${name}`);
    if (!response.ok) {
      throw new NetworkError('Failed to fetch service', {
        statusCode: response.status,
        url: response.url,
        method: 'GET'
      });
    }
    return response.json();
  } catch (error) {
    // Handle and log the error
    handleError(error, {
      component: 'ServiceAPI',
      action: 'fetchService',
      metadata: { serviceName: name }
    });
    throw error;
  }
}

// Connection errors
function handleConnectionFailure() {
  throw new ConnectionError('Failed to connect to launcher', {
    url: 'http://localhost:7000',
    cause: new Error('ECONNREFUSED')
  });
}

// ============================================================================
// RETRY LOGIC
// ============================================================================

// Retry a network operation
async function connectWithRetry() {
  return retry(
    async () => {
      const response = await fetch('http://localhost:7000/health');
      if (!response.ok) {
        throw new Error('Health check failed');
      }
      return response.json();
    },
    {
      maxAttempts: 3,
      delay: 1000,
      backoff: 'exponential',
      shouldRetry: isRetryableError,
      onRetry: (attempt: number, error: Error) => {
        serviceLogger.warn(`Retry attempt ${attempt}`, {
          metadata: { error: error.message }
        });
      }
    }
  );
}

// ============================================================================
// CORRELATION IDs
// ============================================================================

async function processRequest(requestId: string) {
  // Set correlation ID for tracking across operations
  serviceLogger.setCorrelationId(requestId);
  
  serviceLogger.info('Processing request');
  // ... do work ...
  serviceLogger.info('Request completed');
  
  // Clear when done
  serviceLogger.clearCorrelationId();
}

// ============================================================================
// CHILD LOGGERS
// ============================================================================

// Create child loggers for sub-components
const socketLogger = serviceLogger.child('Socket');
socketLogger.info('Socket connected'); // Logs as [ServiceManager:Socket]

const apiLogger = serviceLogger.child('API');
apiLogger.debug('API request sent'); // Logs as [ServiceManager:API]

// ============================================================================
// ERROR BOUNDARY USAGE (React)
// ============================================================================

/*
import { ErrorBoundary } from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      component="App"
      fallback={
        <div>
          <h1>Something went wrong</h1>
          <p>Please refresh the page</p>
        </div>
      }
      onError={(error, errorInfo) => {
        // Custom error handling
        console.error('App error:', error, errorInfo);
      }}
    >
      <YourComponent />
    </ErrorBoundary>
  );
}

// Or wrap a component
const SafeComponent = withErrorBoundary(MyComponent, {
  component: 'MyComponent',
});
*/

// ============================================================================
// RETRIEVING LOGS
// ============================================================================

/*
import { getBufferedLogs, clearBufferedLogs } from '@/lib/observability';

// Get all buffered logs
const logs = getBufferedLogs();
console.log('Recent logs:', logs);

// Clear the buffer
clearBufferedLogs();

// Export logs
function exportLogs() {
  const logs = getBufferedLogs();
  const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `logs-${new Date().toISOString()}.json`;
  a.click();
}
*/

export {};
