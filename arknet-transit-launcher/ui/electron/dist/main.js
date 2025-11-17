"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const path = __importStar(require("path"));
let mainWindow = null;
function createWindow() {
    // Create the browser window
    mainWindow = new electron_1.BrowserWindow({
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
    // Uncomment the next line to open DevTools for debugging
    // mainWindow.webContents.openDevTools();
    // Handle window closed
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
// App event listeners
electron_1.app.whenReady().then(createWindow);
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('activate', () => {
    if (electron_1.BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
// IPC handlers for backend communication
electron_1.ipcMain.handle('get-services-status', async () => {
    try {
        const response = await fetch('http://127.0.0.1:7000/services');
        if (!response.ok)
            throw new Error('Failed to fetch services');
        const services = await response.json();
        // Return the full service list from backend
        return services;
    }
    catch (error) {
        console.error('Error fetching services status:', error);
        return [];
    }
});
electron_1.ipcMain.handle('start-service', async (event, serviceName) => {
    try {
        const response = await fetch(`http://127.0.0.1:7000/services/${serviceName}/start`, { method: 'POST' });
        if (!response.ok)
            throw new Error('Failed to start service');
        const result = await response.json();
        return { success: true, message: result.message };
    }
    catch (error) {
        console.error('Error starting service:', error);
        return { success: false, message: `Failed to start ${serviceName}: ${error.message}` };
    }
});
electron_1.ipcMain.handle('stop-service', async (event, serviceName) => {
    try {
        const response = await fetch(`http://127.0.0.1:7000/services/${serviceName}/stop`, { method: 'POST' });
        if (!response.ok)
            throw new Error('Failed to stop service');
        const result = await response.json();
        return { success: true, message: result.message };
    }
    catch (error) {
        console.error('Error stopping service:', error);
        return { success: false, message: `Failed to stop ${serviceName}: ${error.message}` };
    }
});
