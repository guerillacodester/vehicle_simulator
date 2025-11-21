'use client';

import React, { useState, useEffect } from 'react';
import { TelemetryWallDemo } from '@/core/telemetry/TelemetryWallDemo';
import { TelemetryProvider } from '@/core/telemetry/TelemetryContext';
import { ConnectionStatusIndicator } from '@/core/telemetry/ConnectionStatusIndicator';

function getCookieToken(): string {
  if (typeof document === 'undefined') return '';
  // Try both 'jwt' and 'jwtToken' cookie names
  let match = document.cookie.match(/(^|;)\s*jwt=([^;]+)/);
  if (match) return match[2];
  match = document.cookie.match(/(^|;)\s*jwtToken=([^;]+)/);
  return match ? match[2] : '';
}

export default function TelemetryWallDemoPage() {
  // With httpOnly cookies, we don't need to read or pass the token
  // The browser automatically sends it with requests
  console.log('Telemetry Wall Demo: Using httpOnly cookie authentication');

  const mockRefreshToken = async () => {
    // In production, this would call a refresh endpoint that returns a new httpOnly cookie
    await new Promise(res => setTimeout(res, 500));
    return ''; // Token is in httpOnly cookie, not accessible to JS
  };

  return (
    <TelemetryProvider baseUrl="http://localhost:5000" token={undefined} refreshToken={mockRefreshToken}>
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
          token={undefined}
        />
      </div>
    </TelemetryProvider>
  );
}
