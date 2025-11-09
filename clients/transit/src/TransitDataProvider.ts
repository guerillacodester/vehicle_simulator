import axios from 'axios';
import * as WS from 'ws';
import { RouteSummary, RouteDetail, Vehicle } from './types';

export class TransitDataProvider {
  baseUrl: string;
  wsUrl: string;
  private cache: Map<string, { ts: number; data: any }>; 
  private ws: any;

  constructor(options: { baseUrl?: string; wsUrl?: string } = {}) {
    this.baseUrl = options.baseUrl || 'http://localhost:4001';
    this.wsUrl = options.wsUrl || 'ws://localhost:4001';
    this.cache = new Map();
  }

  async getAllRoutes(): Promise<RouteSummary[]> {
    const key = 'routes';
    const now = Date.now();
    const cached = this.cache.get(key);
    if (cached && now - cached.ts < 60_000) return cached.data;

    const res = await axios.get(`${this.baseUrl}/routes`);
    const data = res.data as RouteSummary[];
    this.cache.set(key, { ts: now, data });
    return data;
  }

  async getRouteDetails(routeId: string): Promise<RouteDetail | null> {
    const res = await axios.get(`${this.baseUrl}/routes/${routeId}`);
    return res.data as RouteDetail;
  }

  // Lightweight subscribe API: callback receives Vehicle[] updates for a route
  subscribeToRoute(routeId: string, callback: (vehicles: Vehicle[]) => void) {
    // ensure ws connection
    if (!this.ws || this.ws.readyState !== 1) {
      this.connectWs();
    }

    const onMessage = (msg: any) => {
      try {
        const parsed = JSON.parse(msg.toString());
        if (parsed.type === 'vehicle:update' && parsed.routeId === routeId) {
          callback(parsed.vehicles as Vehicle[]);
        }
      } catch (e) {
        // ignore parse errors
      }
    };

  this.ws?.on('message', onMessage as any);

    return () => {
      // remove listener when unsubscribing
      this.ws?.removeListener('message', onMessage as any);
    };
  }

  connectWs() {
  if (this.ws && (this.ws.readyState === 1 || this.ws.readyState === 0)) return;
  // runtime constructor from ws module
  this.ws = new (WS as any)(this.wsUrl);
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
