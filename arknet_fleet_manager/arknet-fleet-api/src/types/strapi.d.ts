/**
 * Global Strapi type declarations
 * In Strapi v5, the strapi instance is available as a global variable
 */

import type { Core } from '@strapi/strapi';

declare global {
  var strapi: Core.Strapi;
}

export {};
