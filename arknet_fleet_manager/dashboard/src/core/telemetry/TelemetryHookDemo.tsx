import React from 'react';
import { useTelemetry, TelemetryProvider } from './TelemetryContext';

export const TelemetryHookDemo: React.FC<{ baseUrl: string; token?: string }> = ({ baseUrl, token }) => (
  <TelemetryProvider baseUrl={baseUrl} token={token}>
    <TelemetryHookDemoInner />
  </TelemetryProvider>
);

const TelemetryHookDemoInner: React.FC = () => {
  const { vehicles, connectionState, connectionType } = useTelemetry();

  return (
    <div style={{ padding: 32, fontFamily: 'monospace', background: '#222', color: '#fff' }}>
      <h2>useTelemetry Hook Demo</h2>
      <div>Connection State: <b>{connectionState}</b></div>
      <div>Connection Type: <b>{connectionType}</b></div>
      <div>Vehicle Count: <b>{vehicles.length}</b></div>
      <ul>
        {vehicles.map(v => (
          <li key={v.deviceId}>{v.deviceId}</li>
        ))}
      </ul>
    </div>
  );
}
