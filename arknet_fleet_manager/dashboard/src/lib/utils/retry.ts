/**
 * Retry utility for handling transient failures
 */

import { createComponentLogger } from '@/lib/observability';

const logger = createComponentLogger('RetryUtil');

export interface RetryOptions {
  maxAttempts?: number;
  delay?: number;
  backoff?: 'fixed' | 'exponential' | 'linear';
  maxDelay?: number;
  onRetry?: (attempt: number, error: Error) => void;
  shouldRetry?: (error: Error) => boolean;
}

const DEFAULT_OPTIONS: Required<RetryOptions> = {
  maxAttempts: 3,
  delay: 1000,
  backoff: 'exponential',
  maxDelay: 30000,
  onRetry: () => {},
  shouldRetry: () => true,
};

/**
 * Calculate delay based on backoff strategy
 */
function calculateDelay(attempt: number, options: Required<RetryOptions>): number {
  let delay: number;

  switch (options.backoff) {
    case 'exponential':
      delay = options.delay * Math.pow(2, attempt - 1);
      break;
    case 'linear':
      delay = options.delay * attempt;
      break;
    case 'fixed':
    default:
      delay = options.delay;
      break;
  }

  // Add jitter to prevent thundering herd
  const jitter = Math.random() * 0.3 * delay;
  delay = delay + jitter;

  return Math.min(delay, options.maxDelay);
}

/**
 * Sleep utility
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry an async operation with exponential backoff
 */
export async function retry<T>(
  operation: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const opts: Required<RetryOptions> = { ...DEFAULT_OPTIONS, ...options };
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= opts.maxAttempts; attempt++) {
    try {
      logger.debug(`Attempting operation (attempt ${attempt}/${opts.maxAttempts})`);
      return await operation();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Check if we should retry this error
      if (!opts.shouldRetry(lastError)) {
        logger.warn('Error is not retryable, throwing immediately', {
          metadata: { error: lastError.message }
        });
        throw lastError;
      }

      // If this was the last attempt, throw the error
      if (attempt >= opts.maxAttempts) {
        logger.error('Max retry attempts reached', lastError, {
          metadata: { attempts: attempt }
        });
        throw lastError;
      }

      // Calculate delay and wait
      const delay = calculateDelay(attempt, opts);
      logger.info(`Retry attempt ${attempt} failed, waiting ${delay}ms before retry`, {
        metadata: {
          attempt,
          delay,
          error: lastError.message,
        }
      });

      opts.onRetry(attempt, lastError);
      await sleep(delay);
    }
  }

  // Should never reach here, but TypeScript needs this
  throw lastError || new Error('Retry failed');
}

/**
 * Create a retryable version of a function
 */
export function retryable<T extends (...args: never[]) => Promise<unknown>>(
  fn: T,
  options: RetryOptions = {}
): T {
  return ((...args: Parameters<T>) => {
    return retry(() => fn(...args), options);
  }) as T;
}

/**
 * Check if an error is retryable (common network/timeout errors)
 */
export function isRetryableError(error: Error): boolean {
  const retryableMessages = [
    'timeout',
    'network',
    'ECONNRESET',
    'ECONNREFUSED',
    'ETIMEDOUT',
    'fetch failed',
    'NetworkError',
  ];

  const errorMessage = error.message.toLowerCase();
  return retryableMessages.some(msg => errorMessage.includes(msg.toLowerCase()));
}

/**
 * Check if an HTTP status code is retryable
 */
export function isRetryableStatusCode(statusCode: number): boolean {
  return [408, 429, 500, 502, 503, 504].includes(statusCode);
}
