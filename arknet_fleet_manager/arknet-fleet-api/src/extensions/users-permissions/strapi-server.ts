import authController from './controllers/auth';
import rbacTierPolicy from './policies/rbacTierPolicy';

export default (plugin: any) => {
  plugin.controllers.auth = authController;
  plugin.policies['rbacTierPolicy'] = rbacTierPolicy;
  
  return plugin;
};
