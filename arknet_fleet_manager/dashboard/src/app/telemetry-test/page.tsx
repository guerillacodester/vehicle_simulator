'use client';

import React from 'react';
import { TelemetryTestComponent } from '@/core/telemetry/TelemetryTestComponent';

export default function TelemetryTestPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#1a1a1a', color: '#fff' }}>
      <TelemetryTestComponent 
        baseUrl="http://localhost:5000" 
        token="supersecrettoken"
      />
    </div>
  );
}
