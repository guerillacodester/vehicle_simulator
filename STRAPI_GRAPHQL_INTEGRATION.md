# Strapi GraphQL Integration Guide

**Date**: November 9, 2025
**Decision**: Switch from REST to GraphQL for Strapi access in Next.js dashboard

## Architecture Change

### Before (REST)
```typescript
// REST API calls
fetch('http://localhost:1337/api/routes/14')
fetch('http://localhost:1337/api/depots')
```

### After (GraphQL)
```typescript
// GraphQL queries
const query = `
  query GetRoute($id: ID!) {
    route(id: $id) {
      data {
        id
        attributes {
          short_name
          long_name
          geometry
        }
      }
    }
  }
`;
```

## Strapi GraphQL Configuration

### 1. Enable GraphQL Plugin in Strapi

Strapi has built-in GraphQL support via the `@strapi/plugin-graphql` package.

**Check if installed:**
```bash
cd arknet_fleet_manager/arknet-fleet-api
npm list @strapi/plugin-graphql
```

**If not installed:**
```bash
npm install @strapi/plugin-graphql
```

**GraphQL endpoint:**
- URL: `http://localhost:1337/graphql`
- Playground: `http://localhost:1337/graphql` (in browser)

### 2. Next.js GraphQL Client Setup

**Recommended Stack:**
- **Apollo Client** (most popular, full-featured)
- **urql** (lightweight alternative)
- **graphql-request** (minimalist)

**Installation (Apollo Client):**
```bash
cd arknet_fleet_manager/dashboard
npm install @apollo/client graphql
```

### 3. Apollo Client Configuration

**Create Apollo Provider:**
```typescript
// dashboard/src/lib/apollo-client.ts
import { ApolloClient, InMemoryCache, HttpLink } from '@apollo/client';

const httpLink = new HttpLink({
  uri: process.env.NEXT_PUBLIC_STRAPI_GRAPHQL_URL || 'http://localhost:1337/graphql',
});

export const apolloClient = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});
```

**Wrap App with Provider:**
```typescript
// dashboard/src/app/layout.tsx
import { ApolloProvider } from '@apollo/client';
import { apolloClient } from '@/lib/apollo-client';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ApolloProvider client={apolloClient}>
          {children}
        </ApolloProvider>
      </body>
    </html>
  );
}
```

## GraphQL Query Examples

### Route Queries

**Get Single Route:**
```typescript
// dashboard/src/graphql/queries/routes.ts
import { gql } from '@apollo/client';

export const GET_ROUTE = gql`
  query GetRoute($id: ID!) {
    route(id: $id) {
      data {
        id
        attributes {
          short_name
          long_name
          description
          route_type
          color
          text_color
          # Note: geometry field may need custom resolver
        }
      }
    }
  }
`;

export const GET_ALL_ROUTES = gql`
  query GetAllRoutes {
    routes {
      data {
        id
        attributes {
          short_name
          long_name
          route_type
          color
        }
      }
    }
  }
`;
```

**Usage in Component:**
```typescript
// dashboard/src/app/routes/page.tsx
'use client';

import { useQuery } from '@apollo/client';
import { GET_ALL_ROUTES } from '@/graphql/queries/routes';

export default function RoutesPage() {
  const { loading, error, data } = useQuery(GET_ALL_ROUTES);

  if (loading) return <p>Loading routes...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      {data.routes.data.map((route) => (
        <div key={route.id}>
          <h3>{route.attributes.short_name}</h3>
          <p>{route.attributes.long_name}</p>
        </div>
      ))}
    </div>
  );
}
```

### Depot Queries

```typescript
// dashboard/src/graphql/queries/depots.ts
import { gql } from '@apollo/client';

export const GET_ALL_DEPOTS = gql`
  query GetAllDepots {
    depots {
      data {
        id
        attributes {
          name
          address
          capacity
          location {
            latitude
            longitude
          }
        }
      }
    }
  }
`;

export const GET_DEPOT = gql`
  query GetDepot($id: ID!) {
    depot(id: $id) {
      data {
        id
        attributes {
          name
          address
          capacity
          location {
            latitude
            longitude
          }
        }
      }
    }
  }
`;
```

### Vehicle Queries

```typescript
// dashboard/src/graphql/queries/vehicles.ts
import { gql } from '@apollo/client';

export const GET_ALL_VEHICLES = gql`
  query GetAllVehicles($filters: VehicleFiltersInput) {
    vehicles(filters: $filters) {
      data {
        id
        attributes {
          registration_number
          model
          capacity
          status
          depot {
            data {
              id
              attributes {
                name
              }
            }
          }
        }
      }
    }
  }
`;
```

## 🚨 Route Geometry Caveat

**CRITICAL**: Even with GraphQL, the route geometry issue persists!

The Strapi database still has **fragmented shapes with no ordering**. GraphQL queries will return the same broken data as REST.

**Solutions:**

### Option 1: Custom GraphQL Resolver (Recommended)
Add a custom resolver in Strapi that reads from GeoJSON files:

```typescript
// arknet-fleet-api/src/api/route/resolvers/route.ts
export default {
  Query: {
    routeGeometry: async (parent, args, context) => {
      const { routeCode } = args;
      const fs = require('fs');
      const path = require('path');
      
      const geojsonPath = path.join(
        __dirname,
        `../../../../../../arknet_transit_simulator/data/route_${routeCode}.geojson`
      );
      
      const data = JSON.parse(fs.readFileSync(geojsonPath, 'utf8'));
      
      // Sort by layer and concatenate
      const features = data.features.sort((a, b) => 
        a.properties.layer.localeCompare(b.properties.layer)
      );
      
      const coordinates = features.flatMap(f => f.geometry.coordinates);
      
      return {
        type: 'LineString',
        coordinates,
        pointCount: coordinates.length,
        distance: 13.347 // Route 1 distance in km
      };
    }
  }
};
```

### Option 2: Client-Side GeoJSON Fetch
Fetch GeoJSON files directly from Next.js:

```typescript
// dashboard/src/lib/route-geometry.ts
export async function getRouteGeometry(routeCode: string) {
  // Fetch from geospatial service instead
  const response = await fetch(
    `http://localhost:6000/api/routes/${routeCode}/geometry`
  );
  return response.json();
}
```

### Option 3: Bypass Strapi for Geometry
Use GraphQL for metadata, direct fetch for geometry:

```typescript
// Hybrid approach
const { data: routeMetadata } = useQuery(GET_ROUTE, { variables: { id } });
const geometry = await fetch(`/api/routes/${routeCode}/geometry`).then(r => r.json());
```

## Environment Variables

```bash
# dashboard/.env.local
NEXT_PUBLIC_STRAPI_GRAPHQL_URL=http://localhost:1337/graphql
NEXT_PUBLIC_GEOSPATIAL_API_URL=http://localhost:6000
```

## Migration Checklist

- [ ] Install GraphQL packages in Next.js dashboard
- [ ] Create Apollo Client configuration
- [ ] Set up Apollo Provider in layout
- [ ] Create GraphQL query files for routes, depots, vehicles
- [ ] Replace REST fetch calls with GraphQL queries
- [ ] Test GraphQL endpoint in Strapi playground
- [ ] Implement custom resolver for route geometry OR use geospatial service
- [ ] Update environment variables
- [ ] Test all dashboard pages with GraphQL

## Benefits of GraphQL

✅ **Precise data fetching** - Request only needed fields
✅ **Single request** - Get nested relations in one query
✅ **Type safety** - Generated TypeScript types from schema
✅ **Real-time** - GraphQL subscriptions (future)
✅ **Better caching** - Apollo Client automatic cache normalization

## Resources

- Strapi GraphQL Docs: https://docs.strapi.io/dev-docs/plugins/graphql
- Apollo Client Docs: https://www.apollographql.com/docs/react/
- Strapi GraphQL Playground: http://localhost:1337/graphql

---

**Next Steps:**
1. Install Apollo Client in dashboard
2. Configure Apollo Provider
3. Create query files
4. Migrate REST endpoints to GraphQL queries
5. Handle route geometry properly (see ROUTE_GEOMETRY_BIBLE.md)
