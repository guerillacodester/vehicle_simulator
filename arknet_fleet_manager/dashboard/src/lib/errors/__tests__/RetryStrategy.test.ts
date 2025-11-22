// Unit tests for RetryStrategy with circuit breaker
import { RetryStrategy, CircuitState } from '@/lib/errors/RetryStrategy';

describe('RetryStrategy', () => {
  describe('Basic Retry Logic', () => {
    it('should calculate exponential backoff correctly', () => {
      const strategy = new RetryStrategy({
        initialDelay: 1000,
        maxDelay: 10000,
        backoffMultiplier: 2,
        jitterFactor: 0,
      });

      strategy.recordAttempt();
      expect(strategy.getNextDelay()).toBe(2000); // 1000 * 2^1

      strategy.recordAttempt();
      expect(strategy.getNextDelay()).toBe(4000); // 1000 * 2^2

      strategy.recordAttempt();
      expect(strategy.getNextDelay()).toBe(8000); // 1000 * 2^3
    });

    it('should cap delay at maxDelay', () => {
      const strategy = new RetryStrategy({
        initialDelay: 1000,
        maxDelay: 5000,
        backoffMultiplier: 2,
        jitterFactor: 0,
      });

      for (let i = 0; i < 10; i++) {
        strategy.recordAttempt();
      }

      expect(strategy.getNextDelay()).toBeLessThanOrEqual(5000);
    });

    it('should add jitter to delay', () => {
      const strategy = new RetryStrategy({
        initialDelay: 1000,
        maxDelay: 10000,
        backoffMultiplier: 2,
        jitterFactor: 0.2, // 20% jitter
      });

      strategy.recordAttempt();
      const delay = strategy.getNextDelay();

      // With 20% jitter, delay should be in range [1600, 2400]
      // (base 2000 * (0.8 to 1.2))
      expect(delay).toBeGreaterThanOrEqual(1600);
      expect(delay).toBeLessThanOrEqual(2400);
    });

    it('should reset after successful connection', () => {
      const strategy = new RetryStrategy();

      strategy.recordAttempt();
      strategy.recordAttempt();
      strategy.recordAttempt();

      const stats1 = strategy.getStats();
      expect(stats1.attempts).toBe(3);

      strategy.recordSuccess();

      const stats2 = strategy.getStats();
      expect(stats2.attempts).toBe(0);
      expect(stats2.consecutiveFailures).toBe(0);
    });
  });

  describe('Max Retries', () => {
    it('should allow infinite retries by default', () => {
      const strategy = new RetryStrategy();

      for (let i = 0; i < 100; i++) {
        expect(strategy.canRetry()).toBe(true);
        strategy.recordAttempt();
      }
    });

    it('should respect maxRetries limit', () => {
      const strategy = new RetryStrategy({ maxRetries: 3 });

      expect(strategy.canRetry()).toBe(true);
      strategy.recordAttempt();

      expect(strategy.canRetry()).toBe(true);
      strategy.recordAttempt();

      expect(strategy.canRetry()).toBe(true);
      strategy.recordAttempt();

      expect(strategy.canRetry()).toBe(false);
    });
  });

  describe('Circuit Breaker', () => {
    it('should transition to OPEN after threshold failures', () => {
      const strategy = new RetryStrategy({
        circuitBreakerThreshold: 3,
        circuitBreakerTimeout: 5000,
      });

      const stats1 = strategy.getStats();
      expect(stats1.circuitState).toBe(CircuitState.CLOSED);

      // Record failures
      strategy.recordFailure();
      strategy.recordFailure();
      strategy.recordFailure();

      const stats2 = strategy.getStats();
      expect(stats2.circuitState).toBe(CircuitState.OPEN);
    });

    it('should block retries when circuit is OPEN', () => {
      const strategy = new RetryStrategy({
        circuitBreakerThreshold: 2,
        circuitBreakerTimeout: 60000,
      });

      strategy.recordFailure();
      strategy.recordFailure();

      expect(strategy.canRetry()).toBe(false);
    });

    it('should transition to HALF_OPEN after timeout', (done) => {
      const strategy = new RetryStrategy({
        circuitBreakerThreshold: 2,
        circuitBreakerTimeout: 100, // 100ms timeout
      });

      strategy.recordFailure();
      strategy.recordFailure();

      const stats1 = strategy.getStats();
      expect(stats1.circuitState).toBe(CircuitState.OPEN);
      expect(strategy.canRetry()).toBe(false);

      setTimeout(() => {
        // After timeout, circuit should transition to HALF_OPEN
        expect(strategy.canRetry()).toBe(true);
        const stats2 = strategy.getStats();
        expect(stats2.circuitState).toBe(CircuitState.HALF_OPEN);
        done();
      }, 150);
    });

    it('should close circuit after success in HALF_OPEN', () => {
      const strategy = new RetryStrategy({
        circuitBreakerThreshold: 2,
      });

      strategy.recordFailure();
      strategy.recordFailure();

      const stats1 = strategy.getStats();
      expect(stats1.circuitState).toBe(CircuitState.OPEN);

      strategy.recordSuccess();

      const stats2 = strategy.getStats();
      expect(stats2.circuitState).toBe(CircuitState.CLOSED);
      expect(stats2.consecutiveFailures).toBe(0);
    });
  });

  describe('Statistics', () => {
    it('should track retry statistics accurately', () => {
      const strategy = new RetryStrategy();

      strategy.recordAttempt();
      strategy.recordFailure();
      strategy.recordAttempt();
      strategy.recordFailure();

      const stats = strategy.getStats();

      expect(stats.attempts).toBe(2);
      expect(stats.consecutiveFailures).toBe(2);
      expect(stats.circuitState).toBe(CircuitState.CLOSED);
    });

    it('should calculate time since last attempt', (done) => {
      const strategy = new RetryStrategy();

      strategy.recordAttempt();

      setTimeout(() => {
        const stats = strategy.getStats();
        expect(stats.timeSinceLastAttempt).toBeGreaterThan(50);
        done();
      }, 100);
    });
  });

  describe('Reset', () => {
    it('should fully reset all state', () => {
      const strategy = new RetryStrategy({
        circuitBreakerThreshold: 2,
      });

      strategy.recordAttempt();
      strategy.recordAttempt();
      strategy.recordFailure();
      strategy.recordFailure();

      strategy.reset();

      const stats = strategy.getStats();
      expect(stats.attempts).toBe(0);
      expect(stats.consecutiveFailures).toBe(0);
      expect(stats.circuitState).toBe(CircuitState.CLOSED);
    });
  });
});
