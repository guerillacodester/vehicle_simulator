"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.estimateFeatureCount = exports.streamGeoJSON = void 0;
const fs_1 = __importDefault(require("fs"));
// @ts-ignore - stream-chain doesn't have TypeScript types
const stream_chain_1 = require("stream-chain");
// @ts-ignore - stream-json doesn't have TypeScript types
const stream_json_1 = require("stream-json");
// @ts-ignore - stream-json doesn't have TypeScript types
const StreamArray_1 = require("stream-json/streamers/StreamArray");
// @ts-ignore - stream-json doesn't have TypeScript types
const Pick_1 = require("stream-json/filters/Pick");
/**
 * Stream a GeoJSON file and process features in batches
 *
 * Memory-efficient: Processes one feature at a time, never loads entire file into memory
 * Progress tracking: Emits progress events per batch for real-time UI updates
 *
 * @param filePath - Absolute path to the GeoJSON file
 * @param options - Streaming configuration options
 * @returns Promise with streaming results
 *
 * @example
 * ```typescript
 * const result = await streamGeoJSON('/path/to/building.geojson', {
 *   batchSize: 500,
 *   onBatch: async (features) => {
 *     // Insert batch into database
 *     await strapi.entityService.createMany('api::building.building', { data: features });
 *   },
 *   onProgress: (progress) => {
 *     // Emit Socket.IO progress event
 *     strapi.io.emit('import:progress', progress);
 *   }
 * });
 * ```
 */
async function streamGeoJSON(filePath, options) {
    const batchSize = options.batchSize || 500;
    const startTime = Date.now();
    let currentBatch = [];
    let totalFeatures = 0;
    let totalBatches = 0;
    let streamError = null;
    // Get file size for estimation
    const fileStats = fs_1.default.statSync(filePath);
    const totalFileSize = fileStats.size;
    return new Promise((resolve, reject) => {
        // Check if file exists
        if (!fs_1.default.existsSync(filePath)) {
            const error = new Error(`File not found: ${filePath}`);
            if (options.onError) {
                options.onError(error);
            }
            reject(error);
            return;
        }
        // Create streaming pipeline
        // Pick the "features" array from the GeoJSON object, then stream that array
        const fileStream = fs_1.default.createReadStream(filePath);
        const pipeline = (0, stream_chain_1.chain)([
            fileStream,
            (0, stream_json_1.parser)(),
            (0, Pick_1.pick)({ filter: 'features' }), // Extract the "features" property from GeoJSON
            (0, StreamArray_1.streamArray)() // Stream the features array
        ]);
        // Process each feature from the stream
        pipeline.on('data', async (data) => {
            try {
                // StreamArray emits objects with { key, value }
                // value is the GeoJSON feature
                const feature = data.value;
                // Add feature to current batch
                currentBatch.push(feature);
                totalFeatures++;
                // When batch is full, process it
                if (currentBatch.length >= batchSize) {
                    // Pause stream while processing batch
                    pipeline.pause();
                    try {
                        // Process the batch
                        await options.onBatch([...currentBatch]);
                        totalBatches++;
                        // Get bytes read from file stream
                        const bytesRead = fileStream.bytesRead;
                        // Estimate total features based on bytes read (after first batch)
                        let estimatedTotal = 0;
                        if (totalBatches === 1 && bytesRead > 0) {
                            // First batch - calculate bytes per feature and estimate total
                            const bytesPerFeature = bytesRead / totalFeatures;
                            estimatedTotal = Math.floor(totalFileSize / bytesPerFeature);
                        }
                        else if (totalBatches > 1 && bytesRead > 0) {
                            // Subsequent batches - refine estimate
                            const bytesPerFeature = bytesRead / totalFeatures;
                            estimatedTotal = Math.floor(totalFileSize / bytesPerFeature);
                        }
                        // Emit progress event
                        if (options.onProgress) {
                            options.onProgress({
                                processed: totalFeatures,
                                currentBatch: totalBatches,
                                elapsedTime: Date.now() - startTime,
                                estimatedTotal: estimatedTotal > 0 ? estimatedTotal : undefined,
                                bytesRead
                            });
                        }
                        // Clear batch for next iteration
                        currentBatch = [];
                        // Resume stream
                        pipeline.resume();
                    }
                    catch (batchError) {
                        streamError = batchError;
                        if (options.onError) {
                            options.onError(streamError);
                        }
                        pipeline.destroy();
                    }
                }
            }
            catch (error) {
                streamError = error;
                if (options.onError) {
                    options.onError(streamError);
                }
                pipeline.destroy();
            }
        });
        // Handle stream end
        pipeline.on('end', async () => {
            try {
                // Process remaining features in last batch
                if (currentBatch.length > 0) {
                    await options.onBatch([...currentBatch]);
                    totalBatches++;
                    // Emit final progress
                    if (options.onProgress) {
                        options.onProgress({
                            processed: totalFeatures,
                            currentBatch: totalBatches,
                            elapsedTime: Date.now() - startTime
                        });
                    }
                }
                // Resolve with results
                resolve({
                    success: true,
                    totalFeatures,
                    totalBatches,
                    elapsedTime: Date.now() - startTime
                });
            }
            catch (error) {
                streamError = error;
                if (options.onError) {
                    options.onError(streamError);
                }
                reject(streamError);
            }
        });
        // Handle stream errors
        pipeline.on('error', (error) => {
            streamError = error;
            if (options.onError) {
                options.onError(error);
            }
            reject(error);
        });
    });
}
exports.streamGeoJSON = streamGeoJSON;
/**
 * Estimate total features in GeoJSON file without loading entire file
 * Quickly counts features by streaming through the file
 *
 * @param filePath - Path to GeoJSON file
 * @param sampleSize - Not used anymore, kept for backward compatibility
 * @returns Total feature count
 */
async function estimateFeatureCount(filePath, sampleSize = 100) {
    let totalFeatures = 0;
    return new Promise((resolve, reject) => {
        const pipeline = (0, stream_chain_1.chain)([
            fs_1.default.createReadStream(filePath),
            (0, stream_json_1.parser)(),
            (0, Pick_1.pick)({ filter: 'features' }), // Extract the "features" property from GeoJSON
            (0, StreamArray_1.streamArray)()
        ]);
        pipeline.on('data', (data) => {
            totalFeatures++;
        });
        pipeline.on('end', () => {
            resolve(totalFeatures);
        });
        pipeline.on('close', () => {
            resolve(totalFeatures);
        });
        pipeline.on('error', (error) => {
            reject(error);
        });
    });
}
exports.estimateFeatureCount = estimateFeatureCount;
//# sourceMappingURL=geojson-stream-parser.js.map