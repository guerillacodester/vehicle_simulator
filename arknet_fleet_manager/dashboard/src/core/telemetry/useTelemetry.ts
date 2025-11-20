import { useContext } from 'react';
import { TelemetryContext } from './TelemetryContext';
import { TelemetryVehicle, TelemetryConnectionState, TelemetryConnectionType } from './TelemetryDataProvider';

/**
 * useTelemetry hook
 *
 * Provides real-time vehicle telemetry data from the TelemetryProvider context.
 *
 * @returns {
 *   vehicles: TelemetryVehicle[];
 *   connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';
 *   connectionType: 'websocket' | 'sse';
 *   diagnostics: {
 *     state: string;
 *     connectionType: string;
 *     reconnectAttempts: number;
 *     wsFailures: number;
 *     useSSE: boolean;
 *     vehicleCount: number;
 *   };
 *   error?: Error;
 * }
 *
 * @example
 * // Must be used inside a <TelemetryProvider>
 * const { vehicles, connectionState, diagnostics } = useTelemetry();
 *
 * @see TelemetryProvider
 * @see TelemetryDataProvider
 */

export interface UseTelemetryReturn {
  vehicles: TelemetryVehicle[];
  connectionState: TelemetryConnectionState;
  connectionType: TelemetryConnectionType;
  diagnostics: ReturnType<import('./TelemetryDataProvider').TelemetryDataProvider['getDiagnostics']>;
  error?: Error;
}

export function useTelemetry(): UseTelemetryReturn {
  const context = useContext(TelemetryContext);
  if (!context) {
    throw new Error('useTelemetry must be used within a TelemetryProvider');
  }
  return context;
}
