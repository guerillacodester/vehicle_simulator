# SocketProvider Integration Example

This example demonstrates how to use the reusable `socketProvider.ts` and `authProvider.ts` modules for robust Socket.IO event subscription with authentication and reconnect logic in Electron or Next.js apps.

## Usage

```typescript
import socketProvider from './socketProvider';
import authProvider from './authProvider';

// Connect to backend Socket.IO after authentication
function connectSocket() {
  const session = authProvider.getSession();
  if (!session) {
    console.error('User not authenticated');
    return;
  }

  socketProvider.connect({
    url: 'http://localhost:7000', // Your backend Socket.IO URL
    token: session.jwt,           // Pass JWT for authentication
    maxRetries: 5,                // Optional: max retry attempts
    backoffBase: 1000,            // Optional: initial backoff ms
    backoffMax: 10000             // Optional: max backoff ms
  });

  // Listen for service status events
  socketProvider.on('service_status', (event) => {
    console.log('Service event:', event);
    // Update UI or state as needed
  });

  // Listen for connection events
  socketProvider.on('connect', () => {
    console.log('Socket connected');
  });

  socketProvider.on('disconnect', () => {
    console.log('Socket disconnected');
  });
}

// Call connectSocket after successful login
connectSocket();
```

## Notes
- This pattern works in Electron, Next.js, or any TypeScript app.
- Handles authentication, exponential backoff, and event subscription.
- Easily extend for additional event types or custom logic.
