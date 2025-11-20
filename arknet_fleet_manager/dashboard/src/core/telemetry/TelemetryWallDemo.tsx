import React, { useRef, useEffect, useState } from 'react';
import { useTelemetry, TelemetryProvider } from './TelemetryContext';

// Haversine formula to calculate distance between two lat/lon points in meters
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371000; // Earth's radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return R * c; // Distance in meters
}

export const TelemetryWallDemo: React.FC<{ baseUrl: string; token?: string }> = ({ baseUrl, token }) => (
  <TelemetryProvider baseUrl={baseUrl} token={token}>
    <TelemetryWallDemoInner />
  </TelemetryProvider>
);

const TelemetryWallDemoInner: React.FC = () => {
  const { vehicles, connectionState, connectionType } = useTelemetry();
  
  // Track distances - use state for UI, refs for calculation
  const prevPositionsCache = useRef<Map<string, { lat: number; lon: number }>>(new Map());
  const [distances, setDistances] = useState<Record<string, number>>({});

  // Calculate distances in effect (not during render)
  useEffect(() => {
    vehicles.forEach(v => {
      const prev = prevPositionsCache.current.get(v.deviceId);
      if (prev && (prev.lat !== v.lat || prev.lon !== v.lon)) {
        const distance = haversineDistance(prev.lat, prev.lon, v.lat, v.lon);
        setDistances(prevDistances => {
          const totalDistance = (prevDistances[v.deviceId] || 0) + distance;
          console.log(`[${v.deviceId}] Moved ${distance.toFixed(2)}m, Total: ${totalDistance.toFixed(2)}m (${(totalDistance / 1000).toFixed(3)}km)`);
          return { ...prevDistances, [v.deviceId]: totalDistance };
        });
      }
      prevPositionsCache.current.set(v.deviceId, { lat: v.lat, lon: v.lon });
    });
  }, [vehicles]);

  return (
    <div style={{ minHeight: '100vh', background: '#181818', color: '#fff', padding: '32px' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '24px' }}>Telemetry Wall Display</h1>
      <div style={{ marginBottom: '24px', display: 'flex', gap: '32px' }}>
        <div>
          <span style={{ fontWeight: 'bold' }}>Connection:</span> {connectionState}
        </div>
        <div>
          <span style={{ fontWeight: 'bold' }}>Type:</span> {connectionType}
        </div>
        <div>
          <span style={{ fontWeight: 'bold' }}>Vehicles:</span> {vehicles.length}
        </div>
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '32px',
        alignItems: 'stretch',
      }}>
        {vehicles.map(v => (
          <div key={v.deviceId} style={{
            background: '#222',
            borderRadius: '12px',
            boxShadow: '0 2px 12px #0006',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            minHeight: '260px',
          }}>
            <div style={{ fontSize: '1.3rem', fontWeight: 'bold', color: '#00ff99' }}>{v.deviceId}</div>
            <div><b>Route:</b> {v.route || 'N/A'}</div>
            <div><b>Lat/Lon:</b> {v.lat}, {v.lon}</div>
            <div><b>Speed:</b> {v.speed !== undefined ? `${v.speed} m/s` : 'N/A'}</div>
            <div><b>Heading:</b> {v.heading !== undefined ? `${v.heading}°` : 'N/A'}</div>
            <div style={{ color: '#ffaa00', fontWeight: 'bold' }}>
              <b>Distance:</b> {distances[v.deviceId] 
                ? `${(distances[v.deviceId] / 1000).toFixed(3)} km` 
                : '0.000 km'}
            </div>
            <div><b>Timestamp:</b> {v.timestamp || v.lastSeen || 'N/A'}</div>
            <div><b>Driver:</b> {v.driverName && typeof v.driverName === 'object' ? `${(v.driverName as { first?: string; last?: string }).first ?? ''} ${(v.driverName as { first?: string; last?: string }).last ?? ''}`.trim() : 'N/A'}</div>
            <div><b>Vehicle Reg:</b> {v.vehicleReg || 'N/A'}</div>
          </div>
        ))}
        {vehicles.length === 0 && (
          <div style={{ color: '#888', fontSize: '1.2rem', textAlign: 'center', gridColumn: '1/-1' }}>
            No telemetry data available.
          </div>
        )}
      </div>
    </div>
  );
}
