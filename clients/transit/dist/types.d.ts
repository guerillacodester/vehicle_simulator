export interface RouteSummary {
    id: string;
    name: string;
    shortName?: string;
}
export interface RouteDetail extends RouteSummary {
    code?: string;
    origin?: string;
    destination?: string;
    description?: string;
    stops?: Stop[];
    activeVehicles?: number;
}
export interface Vehicle {
    id: string;
    routeId: string;
    latitude: number;
    longitude: number;
    heading?: number;
    speed?: number;
    timestamp: number;
}
export interface Stop {
    id: string;
    name: string;
    latitude?: number;
    longitude?: number;
    lat?: number;
    lon?: number;
    sequence?: number;
}
