export interface RouteSummary {
    id: string;
    code: string;
    name: string;
    origin: string;
    destination: string;
    activeVehicles?: number;
}
export interface RouteDetail extends RouteSummary {
    geometryUrl?: string;
    stops?: Stop[];
}
export interface Stop {
    id: string;
    name: string;
    lat: number;
    lon: number;
}
export interface Vehicle {
    vehicleId: string;
    routeId: string;
    lat: number;
    lon: number;
    speedKmh?: number;
    heading?: number;
    timestamp?: string;
}
