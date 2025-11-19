import { TelemetryDataProvider, TelemetryVehicle } from './TelemetryDataProvider';

describe('TelemetryDataProvider', () => {
  let provider: TelemetryDataProvider;
  const baseUrl = 'http://localhost:5000';
  const token = 'supersecrettoken';

  beforeEach(() => {
    provider = new TelemetryDataProvider(baseUrl, token);
  });

  it('should start in disconnected state', () => {
    expect(provider.getState()).toBe('disconnected');
    expect(provider.getConnectionType()).toBe('websocket');
  });

  it('should connect via WebSocket and receive vehicle updates', (done) => {
    provider.subscribe((vehicles: TelemetryVehicle[]) => {
      if (vehicles.length > 0) {
        expect(vehicles[0].deviceId).toBeDefined();
        done();
      }
    });
    provider.connect();
  });

  it('should fallback to SSE after repeated WebSocket failures', (done) => {
    // Simulate WebSocket failures
    (provider as any).wsFailures = 3;
    provider.connect();
    setTimeout(() => {
      expect(provider.getConnectionType()).toBe('sse');
      done();
    }, 1000);
  });

  it('should expose diagnostics', () => {
    const diag = provider.getDiagnostics();
    expect(diag).toHaveProperty('state');
    expect(diag).toHaveProperty('connectionType');
    expect(diag).toHaveProperty('reconnectAttempts');
    expect(diag).toHaveProperty('wsFailures');
    expect(diag).toHaveProperty('useSSE');
    expect(diag).toHaveProperty('vehicleCount');
  });

  afterEach(() => {
    provider.disconnect();
  });
});
