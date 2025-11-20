import React from 'react';
import { useTelemetry, TelemetryProvider } from './TelemetryContext';

export const TelemetryWallDemo: React.FC<{ baseUrl: string; token?: string }> = ({ baseUrl, token }) => (
  <TelemetryProvider baseUrl={baseUrl} token={token}>
    <TelemetryWallDemoInner />
  </TelemetryProvider>
);

const TelemetryWallDemoInner: React.FC = () => {
  const { vehicles, connectionState, connectionType } = useTelemetry();

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
