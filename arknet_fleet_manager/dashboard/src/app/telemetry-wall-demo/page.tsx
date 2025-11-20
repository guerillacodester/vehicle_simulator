'use client';

import React from 'react';
import { TelemetryWallDemo } from '@/core/telemetry/TelemetryWallDemo';

export default function TelemetryWallDemoPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#181818', color: '#fff' }}>
      <TelemetryWallDemo 
        baseUrl="http://localhost:5000" 
        token="supersecrettoken"
      />
    </div>
  );
}
