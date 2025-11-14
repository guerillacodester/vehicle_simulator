import { RouteSummary, RouteDetail, Vehicle } from './types';
export declare class TransitDataProvider {
    baseUrl: string;
    wsUrl: string;
    private cache;
    private ws;
    constructor(options?: {
        baseUrl?: string;
        wsUrl?: string;
    });
    getAllRoutes(): Promise<RouteSummary[]>;
    getRouteDetails(routeId: string): Promise<RouteDetail | null>;
    subscribeToRoute(routeId: string, callback: (vehicles: Vehicle[]) => void): () => void;
    connectWs(): void;
}
