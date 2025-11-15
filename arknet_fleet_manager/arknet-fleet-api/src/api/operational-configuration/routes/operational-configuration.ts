import { factories } from '@strapi/strapi';

export default factories.createCoreRouter('api::operational-configuration.operational-configuration' as any, {
	config: {
		find: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
		},
		findOne: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
		},
		create: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
		},
		update: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
		},
		delete: {
			policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
		},
	},
});
