"use strict";
/**
 * Route-Depot Lifecycle Hooks
 * Auto-populate display_name field for better UI display
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    async beforeCreate(event) {
        const { data } = event.params;
        // Keep beforeCreate light; relations may not be resolved yet (docIds vs ids)
    },
    async beforeUpdate(event) {
        var _a, _b, _c;
        const { data } = event.params;
        try {
            // Load current record to determine changes
            const currentData = await strapi.entityService.findOne('api::route-depot.route-depot', event.params.where.id, { populate: ['depot', 'route'] });
            if (currentData) {
                const depotId = data.depot !== undefined ? data.depot : (_a = currentData.depot) === null || _a === void 0 ? void 0 : _a.id;
                const routeId = data.route !== undefined ? data.route : (_b = currentData.route) === null || _b === void 0 ? void 0 : _b.id;
                // Refresh cached names if references changed or names missing
                if (depotId && (data.depot !== undefined || !data.depot_name)) {
                    const depot = await strapi.entityService.findOne('api::depot.depot', depotId, {
                        fields: ['name']
                    });
                    if (depot && depot.name) {
                        data.depot_name = depot.name;
                    }
                }
                if (routeId && (data.route !== undefined || !data.route_short_name)) {
                    const route = await strapi.entityService.findOne('api::route.route', routeId, {
                        fields: ['short_name']
                    });
                    if (route && route.short_name) {
                        data.route_short_name = route.short_name;
                    }
                }
                // Update display_name if depot or distance changed and display_name not explicitly provided
                if (data.display_name === undefined) {
                    const effDepotName = (_c = data.depot_name) !== null && _c !== void 0 ? _c : currentData.depot_name;
                    const effDistance = data.distance_from_route_m !== undefined
                        ? data.distance_from_route_m
                        : currentData.distance_from_route_m;
                    if (effDepotName && effDistance !== undefined) {
                        const roundedDistance = Math.round(effDistance);
                        data.display_name = `${effDepotName} - ${roundedDistance}m`;
                    }
                }
            }
        }
        catch (error) {
            console.error('Failed to auto-update cached names/display for route-depot:', error);
        }
    },
    async afterCreate(event) {
        var _a, _b, _c, _d, _e;
        try {
            const createdId = (_a = event.result) === null || _a === void 0 ? void 0 : _a.id;
            if (!createdId)
                return;
            const rec = await strapi.entityService.findOne('api::route-depot.route-depot', createdId, {
                populate: {
                    route: { fields: ['short_name'] },
                    depot: { fields: ['name'] },
                },
            });
            const data = {};
            const routeShort = (_b = rec === null || rec === void 0 ? void 0 : rec.route_short_name) !== null && _b !== void 0 ? _b : (_c = rec === null || rec === void 0 ? void 0 : rec.route) === null || _c === void 0 ? void 0 : _c.short_name;
            const depotName = (_d = rec === null || rec === void 0 ? void 0 : rec.depot_name) !== null && _d !== void 0 ? _d : (_e = rec === null || rec === void 0 ? void 0 : rec.depot) === null || _e === void 0 ? void 0 : _e.name;
            if (rec.route_short_name == null && routeShort)
                data.route_short_name = routeShort;
            if (rec.depot_name == null && depotName)
                data.depot_name = depotName;
            if (rec.display_name == null && depotName && (rec === null || rec === void 0 ? void 0 : rec.distance_from_route_m) !== undefined) {
                const rounded = Math.round(rec.distance_from_route_m);
                data.display_name = `${depotName} - ${rounded}m`;
            }
            if (Object.keys(data).length > 0) {
                await strapi.entityService.update('api::route-depot.route-depot', createdId, { data });
            }
        }
        catch (error) {
            console.error('Failed in afterCreate to populate cached labels for route-depot:', error);
        }
    },
    async afterUpdate(event) {
        var _a, _b, _c, _d, _e, _f, _g, _h;
        try {
            const updatedId = (_b = (_a = event.result) === null || _a === void 0 ? void 0 : _a.id) !== null && _b !== void 0 ? _b : (_d = (_c = event.params) === null || _c === void 0 ? void 0 : _c.where) === null || _d === void 0 ? void 0 : _d.id;
            if (!updatedId)
                return;
            const rec = await strapi.entityService.findOne('api::route-depot.route-depot', updatedId, {
                populate: {
                    route: { fields: ['short_name'] },
                    depot: { fields: ['name'] },
                },
            });
            const data = {};
            const routeShort = (_e = rec === null || rec === void 0 ? void 0 : rec.route_short_name) !== null && _e !== void 0 ? _e : (_f = rec === null || rec === void 0 ? void 0 : rec.route) === null || _f === void 0 ? void 0 : _f.short_name;
            const depotName = (_g = rec === null || rec === void 0 ? void 0 : rec.depot_name) !== null && _g !== void 0 ? _g : (_h = rec === null || rec === void 0 ? void 0 : rec.depot) === null || _h === void 0 ? void 0 : _h.name;
            if (rec.route_short_name == null && routeShort)
                data.route_short_name = routeShort;
            if (rec.depot_name == null && depotName)
                data.depot_name = depotName;
            if (rec.display_name == null && depotName && (rec === null || rec === void 0 ? void 0 : rec.distance_from_route_m) !== undefined) {
                const rounded = Math.round(rec.distance_from_route_m);
                data.display_name = `${depotName} - ${rounded}m`;
            }
            if (Object.keys(data).length > 0) {
                await strapi.entityService.update('api::route-depot.route-depot', updatedId, { data });
            }
        }
        catch (error) {
            console.error('Failed in afterUpdate to populate cached labels for route-depot:', error);
        }
    }
};
//# sourceMappingURL=lifecycles.js.map