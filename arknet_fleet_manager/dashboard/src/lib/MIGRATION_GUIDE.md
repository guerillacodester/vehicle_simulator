# Migration Guide: Integrating the Logging & Error Handling System

This guide shows how to migrate existing components to use the new production-grade logging and error handling system.

## Table of Contents
1. [ServiceManager Migration](#servicemanager-migration)
2. [Socket Manager Migration](#socket-manager-migration)
3. [React Components Migration](#react-components-migration)
4. [API Calls Migration](#api-calls-migration)

---

## ServiceManager Migration

### Before:
```typescript
// ServiceManager.ts
class ServiceManager {
  constructor() {
    console.log('[ServiceManager] Loaded services:', this.services);
  }

  async startService(name: string) {
    try {
      const response = await fetch(`${this.API_BASE}/services/${name}/start`, {
        method: 'POST'
      });
      if (!response.ok) {
        console.error('Failed to start service');
        return { success: false, message: 'Failed to start service' };
      }
      return { success: true, message: 'Service started' };
    } catch (error) {
      console.error('Error starting service:', error);
      return { success: false, message: 'Network error' };
    }
  }
}
```

### After:
```typescript
// ServiceManager.ts
import { createComponentLogger, NetworkError, handleError, retry, isRetryableError } from '@/lib/observability';

const logger = createComponentLogger('ServiceManager');

class ServiceManager {
  constructor() {
    logger.info('Service manager initialized', {
      action: 'init',
      metadata: { apiBase: this.API_BASE }
    });
  }

  async startService(name: string): Promise<{ success: boolean; message: string }> {
    logger.info(`Starting service: ${name}`, {
      action: 'startService',
      metadata: { serviceName: name }
    });

    try {
      // Use retry logic for network calls
      const response = await retry(
        async () => {
          const res = await fetch(`${this.API_BASE}/services/${name}/start`, {
            method: 'POST'
          });
          if (!res.ok) {
            throw new NetworkError('Failed to start service', {
              statusCode: res.status,
              url: res.url,
              method: 'POST'
            });
          }
          return res;
        },
        {
          maxAttempts: 3,
          shouldRetry: isRetryableError,
          onRetry: (attempt: number) => {
            logger.warn(`Retry attempt ${attempt} for starting service`, {
              action: 'startService',
              metadata: { serviceName: name, attempt }
            });
          }
        }
      );

      logger.info(`Service started successfully: ${name}`, {
        action: 'startService',
        metadata: { serviceName: name }
      });

      return { success: true, message: 'Service started' };

    } catch (error) {
      // Use structured error handling
      handleError(error, {
        component: 'ServiceManager',
        action: 'startService',
        metadata: { serviceName: name }
      });

      return {
        success: false,
        message: error instanceof NetworkError ? error.userMessage : 'Failed to start service'
      };
    }
  }

  // Use timed logging for performance tracking
  async loadServices(): Promise<void> {
    await logger.timed('Load services from API', async () => {
      try {
        const response = await fetch(`${this.API_BASE}/services`);
        if (response.ok) {
          const services = await response.json();
          this.services = services.map((s: { name: string }) => s.name);
          
          logger.info('Services loaded successfully', {
            action: 'loadServices',
            metadata: { count: this.services.length, services: this.services }
          });
        } else {
          throw new NetworkError('Failed to load services', {
            statusCode: response.status,
            url: response.url
          });
        }
      } catch (error) {
        handleError(error, {
          component: 'ServiceManager',
          action: 'loadServices'
        });
        this.services = [];
      }
    });
  }
}
```

---

## Socket Manager Migration

### Before:
```typescript
// BaseSocketManager.ts
async connect(): Promise<void> {
  console.log('[BaseSocketManager] Connecting to', this.config.url);
  
  try {
    this.socket = io(this.config.url, this.config.options);
    // ... connection logic ...
  } catch (error) {
    console.error('[BaseSocketManager] Exception during connect:', error);
    throw error;
  }
}
```

### After:
```typescript
// BaseSocketManager.ts
import { createComponentLogger, ConnectionError, TimeoutError, handleError } from '@/lib/observability';

const logger = createComponentLogger('SocketManager');

async connect(): Promise<void> {
  logger.info('Initiating connection', {
    action: 'connect',
    metadata: { url: this.config.url }
  });

  try {
    this.socket = io(this.config.url, this.config.options);

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        const error = new TimeoutError('Connection timeout', {
          timeout: this.config.options?.timeout || 10000,
          url: this.config.url
        });

        handleError(error, {
          component: 'SocketManager',
          action: 'connect'
        });

        reject(error);
      }, this.config.options?.timeout || 10000);

      this.socket!.once('connect', () => {
        clearTimeout(timeout);
        logger.info('Successfully connected', {
          action: 'connect',
          metadata: { url: this.config.url }
        });
        resolve();
      });

      this.socket!.once('connect_error', (error) => {
        clearTimeout(timeout);
        
        const connError = new ConnectionError('Connection failed', {
          url: this.config.url,
          cause: error
        });

        handleError(connError, {
          component: 'SocketManager',
          action: 'connect'
        });

        reject(connError);
      });
    });

  } catch (error) {
    handleError(error, {
      component: 'SocketManager',
      action: 'connect'
    });
    throw error;
  }
}
```

---

## React Components Migration

### Before:
```tsx
// ServicesPage.tsx
export default function ServicesPage() {
  const handleStart = async (serviceName: string) => {
    try {
      const result = await ServiceManager.startService(serviceName);
      if (!result.success) {
        console.error('Failed:', result.message);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return <div>...</div>;
}
```

### After:
```tsx
// ServicesPage.tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { createComponentLogger, handleError } from '@/lib/observability';

const logger = createComponentLogger('ServicesPage');

function ServicesPageContent() {
  const handleStart = async (serviceName: string) => {
    logger.debug('User initiated service start', {
      action: 'handleStart',
      metadata: { serviceName }
    });

    try {
      const result = await ServiceManager.startService(serviceName);
      
      if (!result.success) {
        logger.warn('Service start failed', {
          action: 'handleStart',
          metadata: { serviceName, reason: result.message }
        });
        // Show user notification
      } else {
        logger.info('Service started successfully', {
          action: 'handleStart',
          metadata: { serviceName }
        });
      }
    } catch (error) {
      handleError(error, {
        component: 'ServicesPage',
        action: 'handleStart',
        metadata: { serviceName }
      });
    }
  };

  return <div>...</div>;
}

// Wrap with error boundary
export default function ServicesPage() {
  return (
    <ErrorBoundary
      component="ServicesPage"
      fallback={
        <div>
          <h2>⚠️ Something went wrong</h2>
          <p>Please refresh the page</p>
        </div>
      }
    >
      <ServicesPageContent />
    </ErrorBoundary>
  );
}
```

---

## API Calls Migration

### Before:
```typescript
async function fetchData(id: string) {
  try {
    const response = await fetch(`/api/data/${id}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
}
```

### After:
```typescript
import { 
  createComponentLogger, 
  NetworkError, 
  NotFoundError,
  handleError,
  retry,
  isRetryableError 
} from '@/lib/observability';

const logger = createComponentLogger('DataService');

async function fetchData(id: string) {
  const correlationId = `fetch-${id}-${Date.now()}`;
  logger.setCorrelationId(correlationId);

  try {
    return await logger.timed(`Fetch data for ${id}`, async () => {
      const response = await retry(
        async () => {
          const res = await fetch(`/api/data/${id}`);
          
          if (res.status === 404) {
            throw new NotFoundError('Data', id);
          }
          
          if (!res.ok) {
            throw new NetworkError('Failed to fetch data', {
              statusCode: res.status,
              url: res.url,
              method: 'GET'
            });
          }
          
          return res;
        },
        {
          maxAttempts: 3,
          shouldRetry: (error) => {
            // Don't retry 404s
            if (error instanceof NotFoundError) return false;
            return isRetryableError(error);
          }
        }
      );

      const data = await response.json();
      
      logger.info('Data fetched successfully', {
        action: 'fetchData',
        metadata: { id, size: JSON.stringify(data).length }
      });

      return data;
    });

  } catch (error) {
    handleError(error, {
      component: 'DataService',
      action: 'fetchData',
      metadata: { id }
    });
    throw error;
  } finally {
    logger.clearCorrelationId();
  }
}
```

---

## Step-by-Step Migration Checklist

### 1. Import the logging system
```typescript
import { createComponentLogger } from '@/lib/observability';
const logger = createComponentLogger('YourComponent');
```

### 2. Replace console.* calls
- ✅ `console.log` → `logger.info` or `logger.debug`
- ✅ `console.warn` → `logger.warn`
- ✅ `console.error` → `logger.error(message, error)`

### 3. Add structured metadata
```typescript
logger.info('Operation completed', {
  action: 'operationName',
  metadata: { key: 'value' }
});
```

### 4. Use structured errors
```typescript
throw new NetworkError('Connection failed', {
  statusCode: 500,
  url: 'http://api.example.com'
});
```

### 5. Wrap error-prone operations with retry
```typescript
await retry(async () => {
  // operation
}, { maxAttempts: 3 });
```

### 6. Use error handler
```typescript
catch (error) {
  handleError(error, {
    component: 'ComponentName',
    action: 'actionName'
  });
}
```

### 7. Wrap React components with ErrorBoundary
```tsx
<ErrorBoundary component="ComponentName">
  <YourComponent />
</ErrorBoundary>
```

### 8. Use performance timing
```typescript
await logger.timed('Expensive operation', async () => {
  // operation
});
```

---

## Migration Priority

1. **High Priority** (Start here):
   - ServiceManager
   - Socket managers
   - API call functions

2. **Medium Priority**:
   - React page components
   - Service-specific components

3. **Low Priority** (Nice to have):
   - UI components
   - Utility functions

---

## Testing the Migration

After migration, verify:

1. Open browser DevTools console
2. Look for colorful, emoji-enhanced logs
3. Check that errors show structured metadata
4. Export logs: `getBufferedLogs()` in console
5. Verify retry logic works (simulate network errors)
6. Test error boundaries (throw error in component)

---

## Common Pitfalls

1. **Don't forget to import**: Import from `@/lib/observability`, not individual files
2. **Use correct log levels**: Don't log everything as ERROR
3. **Include context**: Always add `action` and `metadata`
4. **Don't mix old and new**: Remove all `console.*` calls after migration
5. **Test error boundaries**: Make sure they catch errors properly

---

## Support

For questions or issues with the logging system, see:
- [README_LOGGING.md](./README_LOGGING.md) - Full documentation
- [USAGE_EXAMPLES.ts](./USAGE_EXAMPLES.ts) - Code examples
