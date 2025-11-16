import { contextBridge, ipcRenderer } from 'electron';

// Define the API exposed to the renderer
interface ElectronAPI {
  getServicesStatus: () => Promise<{ [key: string]: 'running' | 'stopped' | 'unknown' }>;
  startService: (serviceName: string) => Promise<{ success: boolean; message: string }>;
  stopService: (serviceName: string) => Promise<{ success: boolean; message: string }>;
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getServicesStatus: () => ipcRenderer.invoke('get-services-status'),
  startService: (serviceName: string) => ipcRenderer.invoke('start-service', serviceName),
  stopService: (serviceName: string) => ipcRenderer.invoke('stop-service', serviceName)
} as ElectronAPI);