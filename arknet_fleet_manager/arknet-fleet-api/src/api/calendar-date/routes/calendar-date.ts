/**
 * calendar-date router
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreRouter('api::calendar-date.calendar-date' as any, {
	config: {
		find: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
		},
		findOne: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
		},
		create: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
		},
		update: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
		},
		delete: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
		},
	},
});
