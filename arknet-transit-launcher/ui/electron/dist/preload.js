"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
electron_1.contextBridge.exposeInMainWorld('electronAPI', {
    getServicesStatus: () => electron_1.ipcRenderer.invoke('get-services-status'),
    startService: (serviceName) => electron_1.ipcRenderer.invoke('start-service', serviceName),
    stopService: (serviceName) => electron_1.ipcRenderer.invoke('stop-service', serviceName)
});
