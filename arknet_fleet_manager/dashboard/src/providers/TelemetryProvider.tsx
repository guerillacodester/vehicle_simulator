// Placeholder for Telemetry Provider
import React, { useEffect, useRef, useState } from 'react';
import { TelemetryContext } from '../contexts/TelemetryContext';
import { SocketConnectionState } from '../interfaces/socket';

const TELEMETRY_WS_URL = process.env.NEXT_PUBLIC_TELEMETRY_WS_URL || 'ws://localhost:5000/ws/telemetry';

export default function TelemetryProvider({ children }: { children: React.ReactNode }) {
  const [connectionState, setConnectionState] = useState<SocketConnectionState>(SocketConnectionState.DISCONNECTED);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout | null = null;

    function connect() {
      setConnectionState(SocketConnectionState.CONNECTING);
      wsRef.current = new WebSocket(TELEMETRY_WS_URL);

      wsRef.current.onopen = () => {
        setConnectionState(SocketConnectionState.CONNECTED);
        reconnectAttempts.current = 0;
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (Array.isArray(data.vehicles)) {
            setVehicles(data.vehicles);
          } else if (data.type === 'vehicle:update' && data.vehicle) {
            setVehicles((prev) => {
              const idx = prev.findIndex((v) => v.deviceId === data.vehicle.deviceId);
              if (idx >= 0) prev[idx] = data.vehicle;
              else prev.push(data.vehicle);
              return [...prev];
            });
          }
        } catch (e) {
          // Ignore parse errors
        }
      };

      wsRef.current.onclose = () => {
        setConnectionState(SocketConnectionState.RECONNECTING);
        reconnectAttempts.current += 1;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeout = setTimeout(connect, delay);
      };

      wsRef.current.onerror = () => {
        setConnectionState(SocketConnectionState.ERROR);
        wsRef.current?.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      wsRef.current?.close();
    };
  }, []);

  return (
    <TelemetryContext.Provider value={{ vehicles, connectionState }}>
      {children}
    </TelemetryContext.Provider>
  );
}