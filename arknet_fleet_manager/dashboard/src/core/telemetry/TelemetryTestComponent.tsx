import React, { useState, useEffect, useRef } from 'react';
import { useTelemetry, TelemetryProvider } from './TelemetryContext';

interface LogEntry {
  timestamp: string;
  type: 'connection' | 'snapshot' | 'update';
  message: string;
  data?: any;
}

const TelemetryTestInner: React.FC = () => {
  const { vehicles, connectionState, connectionType, diagnostics } = useTelemetry();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [mounted, setMounted] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const prevVehiclesRef = useRef<typeof vehicles>([]);
  const prevStateRef = useRef({ state: '', type: '' });

  // Client-side only initialization
  useEffect(() => {
    setMounted(true);
    const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
    setLogs([{
      timestamp,
      type: 'connection',
      message: '🚀 Telemetry Monitor Started',
      data: { status: 'initializing' }
    }]);
  }, []);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Log connection state changes
  useEffect(() => {
    if (!mounted) return;
    
    const prevState = prevStateRef.current;
    const stateKey = `${connectionState}-${connectionType}`;
    const prevKey = `${prevState.state}-${prevState.type}`;
    
    if (stateKey !== prevKey && connectionState) {
      const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
      setLogs(prev => [...prev, {
        timestamp,
        type: 'connection',
        message: `🔌 Connection ${connectionState.toUpperCase()}${connectionType ? ` via ${connectionType}` : ''}`,
        data: { 
          state: connectionState, 
          type: connectionType,
          wsFailures: diagnostics.wsFailures,
          reconnectCount: diagnostics.reconnectCount 
        }
      }]);
      
      prevStateRef.current = { state: connectionState, type: connectionType || '' };
    }
  }, [mounted, connectionState, connectionType, diagnostics]);

  // Log every vehicle update as individual entries - stream ALL updates
  useEffect(() => {
    if (!mounted || vehicles.length === 0) return;

    const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);

    // Log EVERY vehicle update, even if data hasn't changed
    vehicles.forEach(v => {
      setLogs(prevLogs => [...prevLogs, {
        timestamp,
        type: 'update',
        message: `📍 ${v.deviceId}`,
        data: {
          lat: v.lat.toFixed(6),
          lon: v.lon.toFixed(6),
          speed: v.speed !== undefined ? `${v.speed.toFixed(1)} m/s` : 'N/A',
          heading: v.heading !== undefined ? `${v.heading}°` : 'N/A',
          route: v.route || 'N/A',
          timestamp: (v as any).timestamp || (v as any).lastSeen || 'N/A'
        }
      }]);
    });

    prevVehiclesRef.current = vehicles;
  }, [mounted, vehicles]);

  const clearLogs = () => setLogs([]);

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#0a0a0a', 
      color: '#00ff00', 
      fontFamily: 'Consolas, Monaco, monospace',
      padding: '20px'
    }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ 
          borderBottom: '2px solid #00ff00', 
          paddingBottom: '10px', 
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h1 style={{ margin: 0, fontSize: '24px' }}>🛰️ GPSCentCom Telemetry Stream Monitor</h1>
          <div style={{ fontSize: '14px' }}>
            <span style={{ 
              padding: '4px 12px', 
              backgroundColor: connectionState === 'connected' ? '#00ff00' : '#ff0000',
              color: '#000',
              borderRadius: '4px',
              fontWeight: 'bold',
              marginRight: '10px'
            }}>
              {connectionState.toUpperCase()}
            </span>
            <span style={{ color: '#888' }}>via {connectionType || 'N/A'}</span>
          </div>
        </div>

        {/* Stats Panel */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(4, 1fr)', 
          gap: '10px',
          marginBottom: '20px'
        }}>
          <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ color: '#888', fontSize: '12px' }}>VEHICLES</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{vehicles.length}</div>
          </div>
          <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ color: '#888', fontSize: '12px' }}>LOG ENTRIES</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{logs.length}</div>
          </div>
          <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ color: '#888', fontSize: '12px' }}>WS FAILURES</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{diagnostics.wsFailures}</div>
          </div>
          <div style={{ backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ color: '#888', fontSize: '12px' }}>RECONNECTS</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{diagnostics.reconnectCount}</div>
          </div>
        </div>

        {/* Live Stream */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
          {/* Log Stream */}
          <div style={{ backgroundColor: '#1a1a1a', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ 
              padding: '10px 15px', 
              borderBottom: '1px solid #333',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{ fontWeight: 'bold' }}>📡 LIVE DATA STREAM</span>
              <div>
                <label style={{ marginRight: '15px', fontSize: '12px' }}>
                  <input 
                    type="checkbox" 
                    checked={autoScroll} 
                    onChange={(e) => setAutoScroll(e.target.checked)}
                    style={{ marginRight: '5px' }}
                  />
                  Auto-scroll
                </label>
                <button 
                  onClick={clearLogs}
                  style={{ 
                    padding: '4px 12px', 
                    backgroundColor: '#333', 
                    color: '#fff',
                    border: 'none',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '12px'
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
            <div style={{ 
              height: '600px', 
              overflowY: 'auto', 
              padding: '15px',
              fontSize: '13px'
            }}>
              {logs.map((log, idx) => (
                <div 
                  key={idx}
                  style={{ 
                    marginBottom: '12px',
                    paddingBottom: '12px',
                    borderBottom: '1px solid #222'
                  }}
                >
                  <div style={{ color: '#666', marginBottom: '4px' }}>
                    [{log.timestamp}] 
                    <span style={{ 
                      marginLeft: '10px',
                      color: log.type === 'connection' ? '#ff9900' : log.type === 'snapshot' ? '#00ccff' : '#00ff00'
                    }}>
                      {log.message}
                    </span>
                  </div>
                  <pre style={{ 
                    margin: '4px 0 0 40px', 
                    color: '#888',
                    fontSize: '11px',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {JSON.stringify(log.data, null, 2)}
                  </pre>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>

          {/* Current Vehicles */}
          <div style={{ backgroundColor: '#1a1a1a', borderRadius: '4px', border: '1px solid #333' }}>
            <div style={{ 
              padding: '10px 15px', 
              borderBottom: '1px solid #333',
              fontWeight: 'bold'
            }}>
              🚌 ACTIVE VEHICLES
            </div>
            <div style={{ 
              height: '600px', 
              overflowY: 'auto', 
              padding: '15px',
              fontSize: '12px'
            }}>
              {vehicles.map(v => (
                <div 
                  key={v.deviceId}
                  style={{ 
                    marginBottom: '15px',
                    padding: '10px',
                    backgroundColor: '#0f0f0f',
                    borderRadius: '4px',
                    border: '1px solid #222'
                  }}
                >
                  <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#00ff00' }}>
                    {v.deviceId}
                  </div>
                  <div style={{ color: '#888', lineHeight: '1.6' }}>
                    <div>📍 {v.lat.toFixed(6)}, {v.lon.toFixed(6)}</div>
                    <div>🚍 Route: {v.route || 'N/A'}</div>
                    {v.speed !== undefined && <div>⚡ Speed: {v.speed.toFixed(1)} m/s</div>}
                    {v.heading !== undefined && <div>🧭 Heading: {v.heading}°</div>}
                  </div>
                </div>
              ))}
              {vehicles.length === 0 && (
                <div style={{ color: '#666', textAlign: 'center', marginTop: '50px' }}>
                  Waiting for telemetry data...
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Usage: Wrap this in your app or a test page
export const TelemetryTestComponent: React.FC<{ baseUrl: string; token?: string }> = ({ baseUrl, token }) => (
  <TelemetryProvider baseUrl={baseUrl} token={token}>
    <TelemetryTestInner />
  </TelemetryProvider>
);
