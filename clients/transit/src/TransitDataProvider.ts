import axios from 'axios';
import * as WS from 'ws';
import { RouteSummary, RouteDetail, Vehicle, Stop } from './types';

export class TransitDataProvider {
  baseUrl: string;
  wsUrl: string;
  private cache: Map<string, { ts: number; data: any }>; 
  private ws: any;

  constructor(options: { baseUrl?: string; wsUrl?: string } = {}) {
    // Connect to Strapi API (default port 1337)
    this.baseUrl = options.baseUrl || process.env.NEXT_PUBLIC_STRAPI_URL || 'http://localhost:1337/api';
    this.wsUrl = options.wsUrl || process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:1337';
    this.cache = new Map();
  }

  async getAllRoutes(): Promise<RouteSummary[]> {
    const key = 'routes';
    const now = Date.now();
    const cached = this.cache.get(key);
    if (cached && now - cached.ts < 60_000) return cached.data;

    const res = await axios.get(`${this.baseUrl}/routes`);
    
    // Handle Strapi v5 response format from custom controller
    let routes: RouteSummary[];
    if (res.data.data && Array.isArray(res.data.data)) {
      routes = res.data.data.map((item: any) => {
        const attr = item.attributes || {};
        return {
          id: String(item.id),
          code: attr.code || '',
          name: attr.name || '',
          origin: attr.origin || '',
          destination: attr.destination || '',
          activeVehicles: 0,
        };
      });
    } else if (Array.isArray(res.data)) {
      routes = res.data as RouteSummary[];
    } else {
      console.warn('Unexpected API response format:', res.data);
      routes = [];
    }
    
    this.cache.set(key, { ts: now, data: routes });
    return routes;
  }

  async getRouteDetails(routeId: string): Promise<RouteDetail | null> {
    const res = await axios.get(`${this.baseUrl}/routes/${routeId}`);
    
    // Handle custom controller response with GTFS data
    if (res.data.data && res.data.data.attributes) {
      const item = res.data.data;
      const attr = item.attributes;
      
      // Stops come from stop_times via trips (GTFS compliant)
      const stops: Stop[] = (attr.stops || []).map((s: any) => ({
        id: s.id || '',
        name: s.name || '',
        lat: s.lat || 0,
        lon: s.lon || 0,
      }));
      
      return {
        id: String(item.id),
        code: attr.code || '',
        name: attr.name || '',
        origin: attr.origin || '',
        destination: attr.destination || '',
        stops: stops,
        activeVehicles: 0,
      };
    }
    
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
