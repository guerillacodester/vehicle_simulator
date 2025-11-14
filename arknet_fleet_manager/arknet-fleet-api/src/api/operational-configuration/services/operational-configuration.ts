'use strict';

/**
 * operational-configuration service
 */

const { createCoreService } = require('@strapi/strapi').factories;

module.exports = createCoreService('api::operational-configuration.operational-configuration');
