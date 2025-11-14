"use strict";
/**
 * Common types for Socket.IO communication
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ServiceType = exports.ReservoirType = exports.CommuterDirection = void 0;
var CommuterDirection;
(function (CommuterDirection) {
    CommuterDirection["INBOUND"] = "inbound";
    CommuterDirection["OUTBOUND"] = "outbound";
})(CommuterDirection || (exports.CommuterDirection = CommuterDirection = {}));
var ReservoirType;
(function (ReservoirType) {
    ReservoirType["DEPOT"] = "depot";
    ReservoirType["ROUTE"] = "route";
})(ReservoirType || (exports.ReservoirType = ReservoirType = {}));
var ServiceType;
(function (ServiceType) {
    ServiceType["COMMUTER_SERVICE"] = "commuter-service";
    ServiceType["VEHICLE_CONDUCTOR"] = "vehicle-conductor";
    ServiceType["DEPOT_MANAGER"] = "depot-manager";
    ServiceType["SIMULATOR"] = "simulator";
})(ServiceType || (exports.ServiceType = ServiceType = {}));
//# sourceMappingURL=types.js.map