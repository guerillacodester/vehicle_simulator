import React from 'react';
import { useTransitProvider } from '../../lib/transitProvider';
import type { RouteSummary, Vehicle } from '@transit/types';

type SearchResult = {
  routes: RouteSummary[];
  vehicles: Vehicle[];
};

type Props = {
  onSelectRoute?: (route: RouteSummary) => void;
};

export default function RouteSearch({ onSelectRoute }: Props) {
  const provider = useTransitProvider();
  const [query, setQuery] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [results, setResults] = React.useState<SearchResult>({ routes: [], vehicles: [] });

  // Simple search that queries all routes and filters by text match against
  // code, name, origin, destination. Vehicle lookup uses activeVehicles info
  // and requires subscribing to a route to get live positions.
  const doSearch = React.useCallback(async (q: string) => {
    setLoading(true);
    setError(null);
    try {
      const all = await provider.getAllRoutes();
      const lowered = q.trim().toLowerCase();
      const matchedRoutes = lowered
        ? all.filter(r =>
            [r.code, r.name, r.origin, r.destination].join(' ').toLowerCase().includes(lowered)
          )
        : all;

      // For vehicles: keep empty for now
      const vehicles: Vehicle[] = [];

      setResults({ routes: matchedRoutes, vehicles });
    } catch (err) {
      console.error('Failed to fetch routes:', err);
      
      // Handle different error types
      let errorMessage = 'Failed to connect to backend';
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { status: number; statusText: string } };
        if (axiosErr.response?.status === 500) {
          errorMessage = 'Backend server error (500). Check Strapi logs for details.';
        } else if (axiosErr.response?.status) {
          errorMessage = `Backend error: ${axiosErr.response.status} ${axiosErr.response.statusText}`;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setResults({ routes: [], vehicles: [] });
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

      {loading && <div style={{ padding: 8, color: '#888' }}>Searching…</div>}
      {error && (
        <div style={{ 
          padding: 12, 
          background: 'rgba(255, 68, 68, 0.1)', 
          border: '1px solid rgba(255, 68, 68, 0.3)',
          borderRadius: 6, 
          marginBottom: 12,
          color: '#ff6b6b'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 18 }}>⚠️</span>
            <div>
              <strong>Backend Connection Error</strong>
              <div style={{ fontSize: 13, marginTop: 4, opacity: 0.9 }}>
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      <section>
        <h3>Routes ({results.routes.length})</h3>
        {!error && results.routes.length === 0 && !loading && (
          <div style={{ padding: 12, color: '#888', fontStyle: 'italic' }}>
            No routes found. Try a different search term.
          </div>
        )}
        <ul>
          {results.routes.map(r => (
            <li key={r.id} className="route-item" style={{ marginBottom: 6 }}>
              <button onClick={() => onSelectRoute?.(r)} className="route-item-btn">
                <strong>{r.code}</strong> — {r.name}
                <div className="muted"><small>{r.origin} → {r.destination}</small></div>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3>Vehicles ({results.vehicles.length})</h3>
        {results.vehicles.length === 0 && !error && (
          <div style={{ padding: 12, color: '#888', fontStyle: 'italic' }}>
            No live vehicles available
          </div>
        )}
        <ul>
          {results.vehicles.map(v => (
            <li key={v.vehicleId}>{v.vehicleId} — {v.lat.toFixed(5)},{v.lon.toFixed(5)}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
