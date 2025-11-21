import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { TelemetryDataProvider, TelemetryVehicle, TelemetryConnectionState, TelemetryConnectionType } from './TelemetryDataProvider';

interface TelemetryContextValue {
  vehicles: TelemetryVehicle[];
  connectionState: TelemetryConnectionState;
  connectionType: TelemetryConnectionType;
  diagnostics: ReturnType<TelemetryDataProvider['getDiagnostics']>;
}

export const TelemetryContext = createContext<TelemetryContextValue | undefined>(undefined);


export const TelemetryProvider: React.FC<{
  baseUrl: string;
  token?: string;
  refreshToken?: () => Promise<string>;
  children: React.ReactNode;
}> = ({ baseUrl, token, refreshToken, children }) => {
  const providerRef = useRef<TelemetryDataProvider | null>(null);
  const [vehicles, setVehicles] = useState<TelemetryVehicle[]>([]);
  const [connectionState, setConnectionState] = useState<TelemetryConnectionState>('disconnected');
  const [connectionType, setConnectionType] = useState<TelemetryConnectionType>('websocket');
  const [diagnostics, setDiagnostics] = useState<ReturnType<TelemetryDataProvider['getDiagnostics']>>({
    state: 'disconnected',
    connectionType: 'websocket',
    reconnectAttempts: 0,
    wsFailures: 0,
    useSSE: false,
    vehicleCount: 0
  });

  useEffect(() => {
    providerRef.current = new TelemetryDataProvider(baseUrl, token, refreshToken);
    providerRef.current.connect();

    const unsubVehicles = providerRef.current.subscribe(setVehicles);
    const unsubStatus = providerRef.current.onStatus((state) => {
      setConnectionState(state);
      setConnectionType(providerRef.current!.getConnectionType());
      setDiagnostics(providerRef.current!.getDiagnostics());
    });

    return () => {
      unsubVehicles();
      unsubStatus();
      providerRef.current?.disconnect();
    };
  }, [baseUrl, token, refreshToken]);

  return (
    <TelemetryContext.Provider value={{ vehicles, connectionState, connectionType, diagnostics }}>
      {children}
    </TelemetryContext.Provider>
  );
};

export const useTelemetry = () => {
  const ctx = useContext(TelemetryContext);
  if (!ctx) throw new Error('useTelemetry must be used within a TelemetryProvider');
  return ctx;
};
