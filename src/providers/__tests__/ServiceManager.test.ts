import ServiceManager from '../ServiceManager';

describe('ServiceManager', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should start a service successfully', async () => {
    const result = await ServiceManager.startService('gpscentcom');
    expect(result).toEqual({ success: true, message: 'gpscentcom started successfully.' });
  });

  test('should throw an error when starting a non-existent service', async () => {
    await expect(ServiceManager.startService('nonexistent')).rejects.toThrow('Service nonexistent not found.');
  });

  test('should stop a service successfully', async () => {
    const result = await ServiceManager.stopService('gpscentcom');
    expect(result).toEqual({ success: true, message: 'gpscentcom stopped successfully.' });
  });

  test('should throw an error when stopping a non-existent service', async () => {
    await expect(ServiceManager.stopService('nonexistent')).rejects.toThrow('Service nonexistent not found.');
  });

  test('should get the status of a running service', async () => {
    await ServiceManager.startService('simulator');
    const result = await ServiceManager.getServiceStatus('simulator');
    expect(result).toEqual({ success: true, status: 'running' });
  });

  test('should get the status of a stopped service', async () => {
    await ServiceManager.stopService('simulator');
    const result = await ServiceManager.getServiceStatus('simulator');
    expect(result).toEqual({ success: true, status: 'stopped' });
  });

  test('should throw an error when getting the status of a non-existent service', async () => {
    await expect(ServiceManager.getServiceStatus('nonexistent')).rejects.toThrow('Service nonexistent not found.');
  });

  test('should get the statuses of all services', async () => {
    await ServiceManager.startService('gpscentcom');
    const result = await ServiceManager.getAllServiceStatuses();
    expect(result).toEqual({
      success: true,
      statuses: [
        { serviceName: 'gpscentcom', status: 'running' },
        { serviceName: 'simulator', status: 'stopped' },
      ],
    });
  });
});