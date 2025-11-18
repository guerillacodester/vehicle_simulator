import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;

interface ServiceStatus {
  [key: string]: 'running' | 'stopped' | 'unknown';
}

interface ServiceResult {
  success: boolean;
  message: string;
}

function createWindow(): void {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    title: 'ArkNet Transit Launcher',
    icon: path.join(__dirname, 'assets/icon.png') // Add icon later
  });

  // Load the app
  mainWindow.loadFile('dist/renderer/src/index.html');

  // Log when the page is loaded
  mainWindow.webContents.on('did-finish-load', () => {
    console.log('Page loaded successfully');
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Failed to load:', errorCode, errorDescription);
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App event listeners
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for backend communication
ipcMain.handle('get-services-status', async (): Promise<any[]> => {
  try {
    const response = await fetch('http://127.0.0.1:7000/services');
    if (!response.ok) throw new Error('Failed to fetch services');
    const services = await response.json();
    // Return the full service list from backend
    return services;
  } catch (error) {
    console.error('Error fetching services status:', error);
    return [];
  }
});

ipcMain.handle('start-service', async (event: any, serviceName: string): Promise<ServiceResult> => {
  try {
    const response = await fetch(`http://127.0.0.1:7000/services/${serviceName}/start`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to start service');
    const result = await response.json();
    return { success: true, message: result.message };
  } catch (error) {
    console.error('Error starting service:', error);
    return { success: false, message: `Failed to start ${serviceName}: ${(error as Error).message}` };
  }
});

ipcMain.handle('stop-service', async (event: any, serviceName: string): Promise<ServiceResult> => {
  try {
    const response = await fetch(`http://127.0.0.1:7000/services/${serviceName}/stop`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to stop service');
    const result = await response.json();
    return { success: true, message: result.message };
  } catch (error) {
    console.error('Error stopping service:', error);
    return { success: false, message: `Failed to stop ${serviceName}: ${(error as Error).message}` };
  }
});