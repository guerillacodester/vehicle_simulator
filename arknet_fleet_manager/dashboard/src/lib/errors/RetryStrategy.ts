// RetryStrategy: Configurable retry logic with circuit breaker pattern
// Provides exponential backoff, jitter, and circuit breaker to prevent excessive retries

export interface RetryConfig {
  maxRetries?: number; // -1 for infinite retries
  initialDelay?: number; // Initial delay in ms
  maxDelay?: number; // Maximum delay in ms
  backoffMultiplier?: number; // Exponential backoff multiplier
  jitterFactor?: number; // Add randomness to prevent thundering herd (0-1)
  circuitBreakerThreshold?: number; // Number of consecutive failures before opening circuit
  circuitBreakerTimeout?: number; // Time to wait before trying to close circuit (ms)
}

export enum CircuitState {
  CLOSED = 'closed', // Normal operation
  OPEN = 'open', // Too many failures, block attempts
  HALF_OPEN = 'half-open' // Testing if service recovered
}

export class RetryStrategy {
  private config: Required<RetryConfig>;
  private attempts: number = 0;
  private consecutiveFailures: number = 0;
  private circuitState: CircuitState = CircuitState.CLOSED;
  private circuitOpenedAt: number = 0;
  private lastAttemptAt: number = 0;

  constructor(config: RetryConfig = {}) {
    this.config = {
      maxRetries: config.maxRetries ?? -1, // Infinite by default
      initialDelay: config.initialDelay ?? 1000,
      maxDelay: config.maxDelay ?? 30000,
      backoffMultiplier: config.backoffMultiplier ?? 2,
      jitterFactor: config.jitterFactor ?? 0.1,
      circuitBreakerThreshold: config.circuitBreakerThreshold ?? 5,
      circuitBreakerTimeout: config.circuitBreakerTimeout ?? 60000,
    };
  }

  // Calculate next retry delay with exponential backoff and jitter
  getNextDelay(): number {
    const baseDelay = Math.min(
      this.config.initialDelay * Math.pow(this.config.backoffMultiplier, this.attempts),
      this.config.maxDelay
    );

    // Add jitter to prevent thundering herd
    const jitter = baseDelay * this.config.jitterFactor * (Math.random() * 2 - 1);
    return Math.max(0, baseDelay + jitter);
  }

  // Check if we should attempt a retry
  canRetry(): boolean {
    // Check circuit breaker
    if (this.circuitState === CircuitState.OPEN) {
      const timeSinceOpen = Date.now() - this.circuitOpenedAt;
      if (timeSinceOpen >= this.config.circuitBreakerTimeout) {
        // Transition to half-open to test recovery
        this.circuitState = CircuitState.HALF_OPEN;
        console.log('RetryStrategy: Circuit breaker transitioning to HALF_OPEN');
      } else {
        console.log(`RetryStrategy: Circuit breaker OPEN, blocking retry (${Math.round((this.config.circuitBreakerTimeout - timeSinceOpen) / 1000)}s remaining)`);
        return false;
      }
    }

    // Check max retries
    if (this.config.maxRetries >= 0 && this.attempts >= this.config.maxRetries) {
      console.log(`RetryStrategy: Max retries (${this.config.maxRetries}) reached`);
      return false;
    }

    return true;
  }

  // Record a retry attempt
  recordAttempt() {
    this.attempts++;
    this.lastAttemptAt = Date.now();
  }

  // Record a failure
  recordFailure() {
    this.consecutiveFailures++;
    
    // Check if we should open the circuit breaker
    if (
      this.circuitState !== CircuitState.OPEN &&
      this.consecutiveFailures >= this.config.circuitBreakerThreshold
    ) {
      this.circuitState = CircuitState.OPEN;
      this.circuitOpenedAt = Date.now();
      console.warn(`RetryStrategy: Circuit breaker OPEN after ${this.consecutiveFailures} consecutive failures`);
    }
  }

  // Record a success
  recordSuccess() {
    this.attempts = 0;
    this.consecutiveFailures = 0;
    
    if (this.circuitState !== CircuitState.CLOSED) {
      console.log('RetryStrategy: Circuit breaker CLOSED after successful connection');
      this.circuitState = CircuitState.CLOSED;
    }
  }

  // Reset the retry strategy
  reset() {
    this.attempts = 0;
    this.consecutiveFailures = 0;
    this.circuitState = CircuitState.CLOSED;
    this.circuitOpenedAt = 0;
  }

  // Get current retry statistics
  getStats() {
    return {
      attempts: this.attempts,
      consecutiveFailures: this.consecutiveFailures,
      circuitState: this.circuitState,
      canRetry: this.canRetry(),
      nextDelay: this.getNextDelay(),
      timeSinceLastAttempt: this.lastAttemptAt ? Date.now() - this.lastAttemptAt : 0,
    };
  }
}
