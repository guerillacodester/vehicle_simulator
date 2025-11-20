'use client';

import React from 'react';
import { TelemetryWallDemo } from '@/core/telemetry/TelemetryWallDemo';
import { TelemetryProvider } from '@/core/telemetry/TelemetryContext';
import { ConnectionStatusIndicator } from '@/core/telemetry/ConnectionStatusIndicator';

export default function TelemetryWallDemoPage() {
  return (
    <TelemetryProvider baseUrl="http://localhost:5000" token="supersecrettoken">
      <div style={{ minHeight: '100vh', backgroundColor: '#181818', color: '#fff' }}>
        <div style={{ 
          position: 'fixed', 
          top: 20, 
          right: 20, 
          backgroundColor: '#2a2a2a', 
          padding: '12px 20px', 
          borderRadius: 8,
          fontSize: 16,
          fontWeight: 600,
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
        }}>
          <ConnectionStatusIndicator />
        </div>
        <TelemetryWallDemo 
          baseUrl="http://localhost:5000" 
          token="supersecrettoken"
        />
      </div>
    </TelemetryProvider>
  );
}
