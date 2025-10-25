import fs from 'fs';
// @ts-ignore - stream-chain doesn't have TypeScript types
import { chain } from 'stream-chain';
// @ts-ignore - stream-json doesn't have TypeScript types
import { parser } from 'stream-json';
// @ts-ignore - stream-json doesn't have TypeScript types
import { streamArray } from 'stream-json/streamers/StreamArray';

/**
 * Options for streaming GeoJSON parser
 */
export interface StreamingOptions {
  /** Number of features to accumulate before processing (default: 500) */
  batchSize?: number;
  
  /** Callback to process each batch of features */
  onBatch: (features: any[]) => Promise<void>;
  
  /** Callback for progress updates (for Socket.IO) */
  onProgress?: (progress: StreamProgress) => void;
  
  /** Callback for errors */
  onError?: (error: Error) => void;
}

/**
 * Progress information for streaming
 */
export interface StreamProgress {
  processed: number;
  currentBatch: number;
  elapsedTime: number;
}

/**
 * Result of streaming operation
 */
export interface StreamResult {
  success: boolean;
  totalFeatures: number;
  totalBatches: number;
  elapsedTime: number;
  error?: Error;
}

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
export async function streamGeoJSON(
  filePath: string,
  options: StreamingOptions
): Promise<StreamResult> {
  const batchSize = options.batchSize || 500;
  const startTime = Date.now();
  
  let currentBatch: any[] = [];
  let totalFeatures = 0;
  let totalBatches = 0;
  let streamError: Error | null = null;

  return new Promise((resolve, reject) => {
    // Check if file exists
    if (!fs.existsSync(filePath)) {
      const error = new Error(`File not found: ${filePath}`);
      if (options.onError) {
        options.onError(error);
      }
      reject(error);
      return;
    }

    // Create streaming pipeline
    const pipeline = chain([
      fs.createReadStream(filePath),
      parser(),
      streamArray()
    ]);

    // Process each feature from the stream
    pipeline.on('data', async (data: any) => {
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

            // Emit progress event
            if (options.onProgress) {
              options.onProgress({
                processed: totalFeatures,
                currentBatch: totalBatches,
                elapsedTime: Date.now() - startTime
              });
            }

            // Clear batch for next iteration
            currentBatch = [];

            // Resume stream
            pipeline.resume();
          } catch (batchError) {
            streamError = batchError as Error;
            if (options.onError) {
              options.onError(streamError);
            }
            pipeline.destroy();
          }
        }
      } catch (error) {
        streamError = error as Error;
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
      } catch (error) {
        streamError = error as Error;
        if (options.onError) {
          options.onError(streamError);
        }
        reject(streamError);
      }
    });

    // Handle stream errors
    pipeline.on('error', (error: any) => {
      streamError = error;
      if (options.onError) {
        options.onError(error);
      }
      reject(error);
    });
  });
}

/**
 * Estimate total features in GeoJSON file without loading entire file
 * Uses sampling approach: reads first N features and estimates based on file size
 * 
 * @param filePath - Path to GeoJSON file
 * @param sampleSize - Number of features to sample (default: 100)
 * @returns Estimated total feature count
 */
export async function estimateFeatureCount(
  filePath: string,
  sampleSize: number = 100
): Promise<number> {
  const fileStats = fs.statSync(filePath);
  const fileSize = fileStats.size;

  let sampleFeatures = 0;
  let bytesRead = 0;

  return new Promise((resolve, reject) => {
    const pipeline = chain([
      fs.createReadStream(filePath),
      parser(),
      streamArray()
    ]);

    pipeline.on('data', (data: any) => {
      sampleFeatures++;
      bytesRead = pipeline.readableLength;

      // Stop after sampling
      if (sampleFeatures >= sampleSize) {
        pipeline.destroy();
      }
    });

    pipeline.on('close', () => {
      if (sampleFeatures > 0 && bytesRead > 0) {
        // Estimate: (total file size / bytes per feature) * safety factor
        const bytesPerFeature = bytesRead / sampleFeatures;
        const estimatedTotal = Math.floor((fileSize / bytesPerFeature) * 0.9); // 90% safety factor
        resolve(estimatedTotal);
      } else {
        resolve(0);
      }
    });

    pipeline.on('error', (error: any) => {
      reject(error);
    });
  });
}
