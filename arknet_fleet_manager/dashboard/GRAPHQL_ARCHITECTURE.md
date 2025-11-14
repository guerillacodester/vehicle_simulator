# GraphQL Integration Architecture

## Overview

This document outlines the production-grade GraphQL integration between Next.js Dashboard and Strapi CMS.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Next.js Dashboard                      │
├─────────────────────────────────────────────────────────┤
│  React Components                                        │
│    ↓ use hooks                                          │
│  GraphQL Hooks (useQuery, useMutation)                  │
│    ↓ call                                               │
│  GraphQL Client (Apollo/URQL)                           │
│    ↓ HTTP/WS                                            │
├─────────────────────────────────────────────────────────┤
│                   Network Layer                          │
├─────────────────────────────────────────────────────────┤
│  Strapi GraphQL API (http://localhost:1337/graphql)    │
│    - Auto-generated from content types                  │
│    - Authentication via JWT                              │
│    - Real-time via GraphQL Subscriptions (optional)     │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
dashboard/src/
├── lib/
│   └── graphql/
│       ├── client.ts           # GraphQL client configuration
│       ├── queries/            # Query definitions
│       │   ├── routes.ts
│       │   ├── vehicles.ts
│       │   └── depots.ts
│       ├── mutations/          # Mutation definitions
│       │   ├── routes.ts
│       │   └── vehicles.ts
│       ├── fragments/          # Reusable fragments
│       │   └── route.ts
│       └── types.ts            # Generated TypeScript types
├── hooks/
│   └── graphql/                # Custom GraphQL hooks
│       ├── useRoutes.ts
│       ├── useRoute.ts
│       ├── useVehicles.ts
│       └── useCreateRoute.ts
└── providers/
    └── GraphQLProvider.tsx     # Client provider wrapper
```

## Technology Stack

### Option 1: Apollo Client (Recommended for Complex Apps)
- **Pros**: Mature, feature-rich, excellent DevTools, normalized cache
- **Cons**: Larger bundle size, more complex setup
- **Use When**: Need advanced caching, subscriptions, complex state management

### Option 2: URQL (Recommended for Performance)
- **Pros**: Lightweight, extensible, better performance, simpler API
- **Cons**: Less mature ecosystem, fewer plugins
- **Use When**: Need performance, lightweight solution, straightforward queries

### Option 3: GraphQL Request (Simplest)
- **Pros**: Minimal, no caching, tiny bundle
- **Cons**: No built-in caching, manual state management
- **Use When**: Simple queries, external caching (React Query)

## Recommended: URQL + React Query

For this project, we'll use **URQL** for GraphQL operations with **React Query** for advanced caching and state management. This gives us:
- ✅ Lightweight GraphQL client
- ✅ Powerful caching via React Query
- ✅ Excellent TypeScript support
- ✅ Easy testing and mocking
- ✅ Real-time subscriptions (if needed)

## Implementation Steps

1. **Install Dependencies**
   ```bash
   npm install urql graphql
   npm install @tanstack/react-query
   npm install -D @graphql-codegen/cli @graphql-codegen/typescript @graphql-codegen/typescript-operations @graphql-codegen/typescript-urql
   ```

2. **Configure GraphQL Client**
   - Create client with Strapi endpoint
   - Add authentication interceptor
   - Configure caching strategy

3. **Generate TypeScript Types**
   - Use GraphQL Code Generator
   - Auto-generate types from Strapi schema
   - Keep types in sync with backend

4. **Create Query/Mutation Hooks**
   - Wrap URQL hooks with domain logic
   - Add error handling and loading states
   - Implement optimistic updates

5. **Add Provider to App**
   - Wrap app with GraphQLProvider
   - Configure error boundaries
   - Add dev tools in development

## Best Practices

### 1. Type Safety
- **Always** use generated types
- **Never** use `any` for GraphQL responses
- Use fragment colocation for component-specific data

### 2. Error Handling
- Centralized error handling in client
- User-friendly error messages
- Retry logic for transient failures
- Error boundaries for component isolation

### 3. Caching Strategy
- Use normalized cache for entities with IDs
- Document cache for simple queries
- Cache invalidation on mutations
- Optimistic updates for better UX

### 4. Security
- JWT tokens in httpOnly cookies (if possible)
- Or secure localStorage with refresh tokens
- HTTPS in production
- Rate limiting on mutations

### 5. Performance
- Request only needed fields
- Use fragments to avoid over-fetching
- Implement pagination for lists
- Use subscriptions for real-time data (optional)

### 6. Testing
- Mock GraphQL responses in tests
- Use GraphQL MSW for integration tests
- Test error states and loading states
- Test optimistic updates

## Example Usage Pattern

```typescript
// Component
import { useRoutes } from '@/hooks/graphql/useRoutes';

export function RouteList() {
  const { data, loading, error, refetch } = useRoutes();
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div>
      {data?.routes.map(route => (
        <RouteCard key={route.id} route={route} />
      ))}
    </div>
  );
}
```

## Migration from REST

All existing REST API calls should be gradually migrated to GraphQL:

| REST Endpoint | GraphQL Query |
|--------------|---------------|
| GET /api/routes | `routes { ... }` |
| GET /api/routes/:id | `route(id: $id) { ... }` |
| POST /api/routes | `createRoute(input: $input) { ... }` |
| PUT /api/routes/:id | `updateRoute(id: $id, input: $input) { ... }` |
| DELETE /api/routes/:id | `deleteRoute(id: $id) { ... }` |

## Next Steps

1. [ ] Install URQL and React Query
2. [ ] Configure GraphQL Code Generator
3. [ ] Create client configuration
4. [ ] Generate initial types from Strapi
5. [ ] Create base query/mutation hooks
6. [ ] Migrate first component (Routes list)
7. [ ] Add error handling and loading states
8. [ ] Document patterns for team

---

**Last Updated**: November 9, 2025
**Status**: Architecture Defined, Ready for Implementation
