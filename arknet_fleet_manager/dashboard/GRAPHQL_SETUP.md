# GraphQL Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd arknet_fleet_manager/dashboard
npm install
```

This installs:
- `urql` - GraphQL client
- `graphql` - GraphQL core
- `@tanstack/react-query` - Advanced caching
- `@graphql-codegen/*` - Type generation (dev dependencies)

### 2. Configure Environment

Create `.env.local`:

```bash
# Strapi GraphQL endpoint
NEXT_PUBLIC_STRAPI_GRAPHQL_URL=http://localhost:1337/graphql

# Optional: Strapi API token (if authentication required)
NEXT_PUBLIC_STRAPI_API_TOKEN=your-api-token-here
```

### 3. Enable GraphQL in Strapi

GraphQL plugin should already be enabled. Verify at:
`http://localhost:1337/admin/settings/graphql`

Test the GraphQL playground:
`http://localhost:1337/graphql`

### 4. Generate TypeScript Types

```bash
npm run codegen
```

This generates types from your Strapi schema into `src/lib/graphql/__generated__/`

### 5. Wrap App with Provider

Update `src/app/layout.tsx`:

```tsx
import { GraphQLProvider } from '@/lib/graphql/provider';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <GraphQLProvider>
          {children}
        </GraphQLProvider>
      </body>
    </html>
  );
}
```

### 6. Use in Components

```tsx
'use client';

import { useRoutes } from '@/hooks/useRoutes';

export function RoutesList() {
  const { data: routes, isLoading, error } = useRoutes({ limit: 20 });

  if (isLoading) return <div>Loading routes...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {routes?.map(route => (
        <li key={route.id}>
          {route.short_name} - {route.long_name}
        </li>
      ))}
    </ul>
  );
}
```

## 📋 Available Hooks

### Queries

```tsx
// Get all routes with pagination
const { data, isLoading, error } = useRoutes({ limit: 20, start: 0 });

// Get single route by ID
const { data: route } = useRoute({ id: '14' });

// Get route by code (e.g., "1")
const { data: route } = useRouteByCode('1');

// Search routes
const { data: results } = useSearchRoutes('Airport', { limit: 5 });
```

### Mutations

```tsx
// Create route
const { mutate: createRoute, isPending } = useCreateRoute();
createRoute({
  short_name: '2',
  long_name: 'Route 2 - City Center',
  description: 'Runs through downtown',
  color: '#FF0000'
});

// Update route
const { mutate: updateRoute } = useUpdateRoute();
updateRoute({
  id: '14',
  data: { long_name: 'Updated Name' }
});

// Delete route
const { mutate: deleteRoute } = useDeleteRoute();
deleteRoute({ id: '14' });

// Manual refetch
const refetch = useRefetchRoutes();
refetch();
```

## 🔧 NPM Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "codegen": "graphql-codegen --config codegen.ts",
    "codegen:watch": "graphql-codegen --config codegen.ts --watch"
  }
}
```

## 📁 File Structure

```
dashboard/src/
├── lib/
│   └── graphql/
│       ├── client.ts              # URQL client configuration
│       ├── provider.tsx           # GraphQL provider component
│       ├── queries/               # Query definitions
│       │   └── routes.ts
│       ├── mutations/             # Mutation definitions
│       │   └── routes.ts
│       └── __generated__/         # Auto-generated types (gitignore)
├── hooks/
│   └── useRoutes.ts              # Custom route hooks
└── app/
    ├── layout.tsx                # Add GraphQLProvider here
    └── routes/
        └── page.tsx              # Use hooks in pages
```

## 🔐 Authentication

### With JWT Token

```tsx
// After login, store token
localStorage.setItem('strapi_jwt', token);

// The client will automatically add it to requests
// See: src/lib/graphql/client.ts customFetch()
```

### With API Token

Set in `.env.local`:
```bash
NEXT_PUBLIC_STRAPI_API_TOKEN=your-token
```

Update `client.ts`:
```typescript
const token = process.env.NEXT_PUBLIC_STRAPI_API_TOKEN;
if (token) {
  headers['Authorization'] = `Bearer ${token}`;
}
```

## 🐛 Debugging

### GraphQL Playground

Test queries at: `http://localhost:1337/graphql`

Example query:
```graphql
query {
  routes(pagination: { limit: 5 }) {
    data {
      id
      short_name
      long_name
    }
  }
}
```

### React Query DevTools

Automatically enabled in development at bottom-right of page.
Shows:
- Active queries
- Cache status
- Query timeline
- Manual refetch

### Network Tab

Check browser DevTools → Network → Filter "graphql"
- Request headers (auth)
- Response data
- Errors

## ⚠️ Important Notes

### Route Geometry

**DO NOT use Strapi geometry field for complete routes!**

The database is fragmented. Read: `/ROUTE_GEOMETRY_BIBLE.md`

For route geometry, use GeoJSON files:
```typescript
// Correct way to get route geometry
const response = await fetch(`/api/routes/${routeCode}/geometry`);
const { geometry } = await response.json();
// geometry.coordinates = 418 points for Route 1
```

### Caching

- Queries cached for 5 minutes by default
- Mutations auto-invalidate related queries
- Manual invalidation with `useRefetchRoutes()`

### Error Handling

Errors are logged to console and thrown to components.
Use error boundaries:

```tsx
<ErrorBoundary fallback={<ErrorPage />}>
  <RoutesList />
</ErrorBoundary>
```

## 🧪 Testing

### Mock GraphQL Responses

```tsx
import { createMockClient } from 'urql';

const mockClient = createMockClient({
  executeQuery: vi.fn(() => ({
    data: { routes: { data: [/* mock data */] } }
  }))
});
```

### Integration Tests

Use MSW (Mock Service Worker):

```typescript
import { graphql } from 'msw';

const handlers = [
  graphql.query('GetRoutes', (req, res, ctx) => {
    return res(
      ctx.data({
        routes: {
          data: [
            { id: '1', short_name: '1', long_name: 'Test Route' }
          ]
        }
      })
    );
  })
];
```

## 🚀 Production Checklist

- [ ] Replace localStorage with httpOnly cookies for JWT
- [ ] Enable HTTPS
- [ ] Add rate limiting
- [ ] Configure CORS properly
- [ ] Add error tracking (Sentry)
- [ ] Optimize bundle size (tree shaking)
- [ ] Add request compression
- [ ] Configure CDN for static assets
- [ ] Add monitoring (response times)
- [ ] Set up CI/CD for type generation

---

**Last Updated**: November 9, 2025
**Status**: ✅ Ready for Development
