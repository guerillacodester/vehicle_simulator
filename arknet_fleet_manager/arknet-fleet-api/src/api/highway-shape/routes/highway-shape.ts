/**
 * highway-shape router
 */

import { factories } from '@strapi/strapi'

export default factories.createCoreRouter('api::highway-shape.highway-shape' as any, {
	config: {
		find: { policies: [{ name: 'global::check-access-tier', config: {} }], auth: { scope: ['admin'] } },
		findOne: { policies: [{ name: 'global::check-access-tier', config: {} }], auth: { scope: ['admin'] } },
		create: { policies: [{ name: 'global::check-access-tier', config: {} }], auth: { scope: ['admin'] } },
		update: { policies: [{ name: 'global::check-access-tier', config: {} }], auth: { scope: ['admin'] } },
		delete: { policies: [{ name: 'global::check-access-tier', config: {} }], auth: { scope: ['admin'] } },
	}
});
