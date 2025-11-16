// Test zlib functions
const zlib = require('zlib');
const { promisify } = require('util');

console.log('Testing zlib functions...');

// Test direct access
console.log('zlib.gzip:', typeof zlib.gzip);
console.log('zlib.gunzip:', typeof zlib.gunzip);

// Test promisify
const gzipAsync = promisify(zlib.gzip);
const gunzipAsync = promisify(zlib.gunzip);

console.log('gzipAsync:', typeof gzipAsync);
console.log('gunzipAsync:', typeof gunzipAsync);

// Test functionality
const testData = 'Hello World! This is test data for compression.';
console.log('Original data length:', testData.length);

gzipAsync(Buffer.from(testData))
  .then(compressed => {
    console.log('Compressed length:', compressed.length);
    return gunzipAsync(compressed);
  })
  .then(decompressed => {
    console.log('Decompressed:', decompressed.toString());
    console.log('Round-trip successful:', decompressed.toString() === testData);
  })
  .catch(err => {
    console.error('Error:', err);
  });