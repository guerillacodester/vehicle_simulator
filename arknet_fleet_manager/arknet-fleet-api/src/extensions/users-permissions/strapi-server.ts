import authController from './controllers/auth';

export default (plugin: any) => {
  plugin.controllers.auth = authController;
  
  return plugin;
};
