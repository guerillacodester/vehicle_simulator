import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::route-depot.route-depot' as any, ({ strapi }) => ({
	async debugColumns(ctx) {
		try {
			const knex = (strapi as any).db?.connection;
			const info = await knex('route_depots').columnInfo();
			ctx.body = info;
		} catch (err) {
			ctx.status = 500;
			ctx.body = { status: 'error', message: (err as Error).message };
		}
	},
		async backfillLabels(ctx) {
		try {
					const knex = (strapi as any).db?.connection;
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

						if (!(needsRoute || needsDepot || needsDisplay)) continue;

						let routeShort: string | null = row.route_short_name;
						let depotName: string | null = row.depot_name;

						if (needsRoute) {
							const r = await knex('routes').select('short_name').where({ id: row.route_id }).first();
							routeShort = r?.short_name ?? null;
						}

						if (needsDepot) {
							const d = await knex('depots').select('name').where({ id: row.depot_id }).first();
							depotName = d?.name ?? null;
						}

						const dataToUpdate: any = {};
						if (needsRoute && routeShort) dataToUpdate.route_short_name = routeShort;
						if (needsDepot && depotName) dataToUpdate.depot_name = depotName;
						if (needsDisplay && depotName) {
							dataToUpdate.display_name = `${depotName} - ${Math.round(row.distance_from_route_m)}m`;
						}

						if (Object.keys(dataToUpdate).length > 0) {
							await knex('route_depots').where({ id: row.id }).update(dataToUpdate);
							updated += 1;
						}
					}

					ctx.body = { status: 'ok', updated };
		} catch (err) {
			ctx.status = 500;
			ctx.body = { status: 'error', message: (err as Error).message };
		}
	},
}));
