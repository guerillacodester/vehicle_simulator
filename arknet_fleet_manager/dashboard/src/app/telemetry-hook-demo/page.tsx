'use client';

import React from 'react';
import { TelemetryHookDemo } from '@/core/telemetry/TelemetryHookDemo';

export default function TelemetryHookDemoPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#222', color: '#fff' }}>
      <TelemetryHookDemo 
        baseUrl="http://localhost:5000" 
        token="supersecrettoken"
      />
    </div>
  );
}
