import React from 'react';
import { renderHook } from '@testing-library/react-hooks';
import { TelemetryProvider } from '../TelemetryContext';
import { useTelemetry } from '../useTelemetry';

// Mock context value
const mockTelemetry = {
  vehicles: [{ deviceId: 'TEST001', lat: 1, lon: 2, speed: 3, heading: 4, route: 'A' }],
  connectionState: 'connected',
  connectionType: 'websocket',
  diagnostics: { wsFailures: 0, reconnectCount: 0 },
  error: null
};

// Helper to wrap hook in provider
const wrapper = ({ children }: { children: React.ReactNode }) => (
  <TelemetryProvider baseUrl="http://localhost:5000" token="test">
    {children}
  </TelemetryProvider>
);

describe('useTelemetry', () => {
  it('throws error if used outside provider', () => {
    // Suppress error output
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useTelemetry())).toThrow();
    spy.mockRestore();
  });

  it('returns context value inside provider', () => {
    const { result } = renderHook(() => useTelemetry(), { wrapper });
    expect(result.current).toHaveProperty('vehicles');
    expect(result.current).toHaveProperty('connectionState');
    expect(result.current).toHaveProperty('diagnostics');
    expect(result.current).toHaveProperty('connectionType');
  });
});
