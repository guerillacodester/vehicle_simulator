// setupTests.ts
// Add any global test setup here (e.g., jest-dom, mock fetch, etc.)
import '@testing-library/jest-dom';
// Polyfill EventSource for Jest
// @ts-ignore
global.EventSource = require('eventsource').EventSource;
