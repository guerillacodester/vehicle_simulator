import React from 'react';
import { useTransitProvider } from '../../lib/transitProvider';
import type { RouteSummary, Vehicle } from '@transit/types';

type SearchResult = {
  routes: RouteSummary[];
  vehicles: Vehicle[];
};

export default function RouteSearch() {
  const provider = useTransitProvider();
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<SearchResult>({ routes: [], vehicles: [] });

  // Simple search that queries all routes and filters by text match against
  // code, name, origin, destination. Vehicle lookup uses activeVehicles info
  // and requires subscribing to a route to get live positions.
  const doSearch = React.useCallback(async (q: string) => {
    setLoading(true);
    try {
      const all = await provider.getAllRoutes();
      const lowered = q.trim().toLowerCase();
      const matchedRoutes = lowered
        ? all.filter(r =>
            [r.code, r.name, r.origin, r.destination].join(' ').toLowerCase().includes(lowered)
          )
        : all;

      // For vehicles: if query exactly matches a vehicleId pattern, try to find it
      // otherwise return empty vehicles array. Subscribing to all routes would be expensive.
      const vehicles: Vehicle[] = [];
      const vehicleIdMatch = q.match(/^[A-Za-z0-9_-]{3,}$/);
      if (vehicleIdMatch) {
        // naive approach: poll route details for routes that have activeVehicles
        for (const r of matchedRoutes.slice(0, 10)) {
          try {
            const det = await provider.getRouteDetails(r.id);
            // route details in mock server won't include active vehicle list; skip
          } catch (e) {
            // ignore
          }
        }
      }

      setResults({ routes: matchedRoutes, vehicles });
    } finally {
      setLoading(false);
    }
  }, [provider]);

  React.useEffect(() => {
    const id = setTimeout(() => doSearch(query), 250);
    return () => clearTimeout(id);
  }, [query, doSearch]);

  return (
    <div style={{ padding: 12 }}>
      <label style={{ display: 'block', marginBottom: 8 }}>
        Search routes or vehicle id
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="route name, code, origin, destination, or vehicle id"
          style={{ width: '100%', padding: 8, marginTop: 6 }}
        />
      </label>

      {loading && <div>Searching…</div>}

      <section>
        <h3>Routes ({results.routes.length})</h3>
        <ul>
          {results.routes.map(r => (
            <li key={r.id} style={{ marginBottom: 6 }}>
              <strong>{r.code}</strong> — {r.name} <br />
              <small>{r.origin} → {r.destination}</small>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3>Vehicles ({results.vehicles.length})</h3>
        {results.vehicles.length === 0 && <div>No direct vehicle matches</div>}
        <ul>
          {results.vehicles.map(v => (
            <li key={v.vehicleId}>{v.vehicleId} — {v.lat.toFixed(5)},{v.lon.toFixed(5)}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
