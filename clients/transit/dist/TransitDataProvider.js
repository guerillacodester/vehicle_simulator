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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TransitDataProvider = void 0;
const axios_1 = __importDefault(require("axios"));
const WS = __importStar(require("ws"));
class TransitDataProvider {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || 'http://localhost:4001';
        this.wsUrl = options.wsUrl || 'ws://localhost:4001';
        this.cache = new Map();
    }
    async getAllRoutes() {
        const key = 'routes';
        const now = Date.now();
        const cached = this.cache.get(key);
        if (cached && now - cached.ts < 60000)
            return cached.data;
        const res = await axios_1.default.get(`${this.baseUrl}/routes`);
        const data = res.data;
        this.cache.set(key, { ts: now, data });
        return data;
    }
    async getRouteDetails(routeId) {
        const res = await axios_1.default.get(`${this.baseUrl}/routes/${routeId}`);
        return res.data;
    }
    // Lightweight subscribe API: callback receives Vehicle[] updates for a route
    subscribeToRoute(routeId, callback) {
        // ensure ws connection
        if (!this.ws || this.ws.readyState !== 1) {
            this.connectWs();
        }
        const onMessage = (msg) => {
            try {
                const parsed = JSON.parse(msg.toString());
                if (parsed.type === 'vehicle:update' && parsed.routeId === routeId) {
                    callback(parsed.vehicles);
                }
            }
            catch (e) {
                // ignore parse errors
            }
        };
        this.ws?.on('message', onMessage);
        return () => {
            // remove listener when unsubscribing
            this.ws?.removeListener('message', onMessage);
        };
    }
    connectWs() {
        if (this.ws && (this.ws.readyState === 1 || this.ws.readyState === 0))
            return;
        // runtime constructor from ws module
        this.ws = new WS(this.wsUrl);
        this.ws.on('open', () => {
            // no-op
        });
        this.ws.on('close', () => {
            // try reconnect after delay
            setTimeout(() => this.connectWs(), 2000);
        });
        this.ws.on('error', () => {
            // ignore
        });
    }
}
exports.TransitDataProvider = TransitDataProvider;
