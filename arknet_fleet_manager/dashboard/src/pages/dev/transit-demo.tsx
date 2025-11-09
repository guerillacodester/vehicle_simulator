import React from 'react';
import { useEffect, useState } from 'react';
import { useTransitProvider } from '@/lib/transitProvider';
import type { RouteSummary } from '@transit/types';

export default function TransitDemoPage() {
  const provider = useTransitProvider();
  const [routes, setRoutes] = useState<RouteSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    provider.getAllRoutes().then(r => {
      if (mounted) setRoutes(r);
    }).catch(() => {}).finally(() => mounted && setLoading(false));
    return () => { mounted = false };
  }, [provider]);

  return (
    <div style={{ padding: 16 }}>
      <h1>Transit demo</h1>
      {loading && <p>Loading...</p>}
      <ul>
        {routes.map(r => (
          <li key={r.id}>{r.code} — {r.name} ({r.origin} → {r.destination})</li>
        ))}
      </ul>
    </div>
  );
}
