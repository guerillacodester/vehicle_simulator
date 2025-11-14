"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
exports.default = strapi_1.factories.createCoreController('api::route-depot.route-depot', ({ strapi }) => ({
    async debugColumns(ctx) {
        var _a;
        try {
            const knex = (_a = strapi.db) === null || _a === void 0 ? void 0 : _a.connection;
            const info = await knex('route_depots').columnInfo();
            ctx.body = info;
        }
        catch (err) {
            ctx.status = 500;
            ctx.body = { status: 'error', message: err.message };
        }
    },
    async backfillLabels(ctx) {
        var _a, _b, _c;
        try {
            const knex = (_a = strapi.db) === null || _a === void 0 ? void 0 : _a.connection;
            if (!knex) {
                ctx.status = 500;
                ctx.body = { status: 'error', message: 'Database connection not available' };
                return;
            }
            const rows = await knex('route_depots')
                .select('id', 'route_id', 'depot_id', 'distance_from_route_m', 'route_short_name', 'depot_name', 'display_name')
                .limit(1000);
            let updated = 0;
            for (const row of rows) {
                const needsRoute = row.route_short_name == null && row.route_id != null;
                const needsDepot = row.depot_name == null && row.depot_id != null;
                const needsDisplay = row.display_name == null && row.depot_id != null && row.distance_from_route_m != null;
                if (!(needsRoute || needsDepot || needsDisplay))
                    continue;
                let routeShort = row.route_short_name;
                let depotName = row.depot_name;
                if (needsRoute) {
                    const r = await knex('routes').select('short_name').where({ id: row.route_id }).first();
                    routeShort = (_b = r === null || r === void 0 ? void 0 : r.short_name) !== null && _b !== void 0 ? _b : null;
                }
                if (needsDepot) {
                    const d = await knex('depots').select('name').where({ id: row.depot_id }).first();
                    depotName = (_c = d === null || d === void 0 ? void 0 : d.name) !== null && _c !== void 0 ? _c : null;
                }
                const dataToUpdate = {};
                if (needsRoute && routeShort)
                    dataToUpdate.route_short_name = routeShort;
                if (needsDepot && depotName)
                    dataToUpdate.depot_name = depotName;
                if (needsDisplay && depotName) {
                    dataToUpdate.display_name = `${depotName} - ${Math.round(row.distance_from_route_m)}m`;
                }
                if (Object.keys(dataToUpdate).length > 0) {
                    await knex('route_depots').where({ id: row.id }).update(dataToUpdate);
                    updated += 1;
                }
            }
            ctx.body = { status: 'ok', updated };
        }
        catch (err) {
            ctx.status = 500;
            ctx.body = { status: 'error', message: err.message };
        }
    },
}));
//# sourceMappingURL=route-depot.js.map