// Unit tests for ErrorRecovery strategies
import { ErrorRecovery } from '@/lib/errors/ErrorRecovery';
import { AppError, ErrorCategory, ErrorSeverity } from '@/lib/errors/AppError';
import { ErrorCodes } from '@/lib/errors/ErrorCodes';

describe('ErrorRecovery', () => {
  describe('getRecoveryAction', () => {
    it('should recommend retry for network errors', () => {
      const error = new AppError(
        'Network error',
        {
          category: ErrorCategory.NETWORK,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.NETWORK_ERROR,
          metadata: { details: 'Connection lost' },
        }
      );

      const action = ErrorRecovery.getRecoveryAction(error);

      expect(action.type).toBe('retry');
      expect(action.canAutoRecover).toBe(true);
      expect(action.delay).toBeDefined();
    });

    it('should recommend refresh-auth for expired tokens', () => {
      const error = new AppError(
        'Token expired',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.TOKEN_EXPIRED,
          metadata: { details: 'Session expired' },
        }
      );

      const action = ErrorRecovery.getRecoveryAction(error);

      expect(action.type).toBe('refresh-auth');
      expect(action.canAutoRecover).toBe(true);
    });

    it('should recommend user-action for auth errors', () => {
      const error = new AppError(
        'Authentication failed',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.AUTH_ERROR,
          metadata: { details: 'Invalid credentials' },
        }
      );

      const action = ErrorRecovery.getRecoveryAction(error);

      expect(action.type).toBe('user-action');
      expect(action.canAutoRecover).toBe(false);
    });

    it('should recommend fallback for server errors', () => {
      const error = new AppError(
        'Server error',
        {
          category: ErrorCategory.SYSTEM,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.SERVER_ERROR,
          metadata: { details: 'Internal server error' },
        }
      );

      const action = ErrorRecovery.getRecoveryAction(error);

      expect(action.type).toBe('fallback');
      expect(action.canAutoRecover).toBe(true);
    });

    it('should handle unknown errors gracefully', () => {
      const error = new Error('Unknown error');

      const action = ErrorRecovery.getRecoveryAction(error);

      expect(action.type).toBe('retry');
      expect(action.canAutoRecover).toBe(true);
    });
  });

  describe('isTransientError', () => {
    it('should identify network errors as transient', () => {
      const error = new AppError(
        'Network error',
        {
          category: ErrorCategory.NETWORK,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.NETWORK_ERROR,
        }
      );

      expect(ErrorRecovery.isTransientError(error)).toBe(true);
    });

    it('should identify token expiration as transient', () => {
      const error = new AppError(
        'Token expired',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.TOKEN_EXPIRED,
        }
      );

      expect(ErrorRecovery.isTransientError(error)).toBe(true);
    });

    it('should identify auth errors as non-transient', () => {
      const error = new AppError(
        'Auth failed',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.AUTH_ERROR,
        }
      );

      expect(ErrorRecovery.isTransientError(error)).toBe(false);
    });

    it('should assume unknown errors are transient', () => {
      const error = new Error('Unknown error');

      expect(ErrorRecovery.isTransientError(error)).toBe(true);
    });
  });

  describe('requiresUserAction', () => {
    it('should identify auth errors as requiring user action', () => {
      const error = new AppError(
        'Auth failed',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.AUTH_ERROR,
        }
      );

      expect(ErrorRecovery.requiresUserAction(error)).toBe(true);
    });

    it('should identify network errors as not requiring user action', () => {
      const error = new AppError(
        'Network error',
        {
          category: ErrorCategory.NETWORK,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.NETWORK_ERROR,
        }
      );

      expect(ErrorRecovery.requiresUserAction(error)).toBe(false);
    });

    it('should return false for unknown errors', () => {
      const error = new Error('Unknown error');

      expect(ErrorRecovery.requiresUserAction(error)).toBe(false);
    });
  });

  describe('getUserMessage', () => {
    it('should return user-friendly message for network errors', () => {
      const error = new AppError(
        'Network error',
        {
          category: ErrorCategory.NETWORK,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.NETWORK_ERROR,
        }
      );

      const message = ErrorRecovery.getUserMessage(error);

      expect(message).toContain('Network');
      expect(message).toContain('reconnect');
    });

    it('should return user-friendly message for auth errors', () => {
      const error = new AppError(
        'Auth failed',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.AUTH_ERROR,
        }
      );

      const message = ErrorRecovery.getUserMessage(error);

      expect(message).toContain('Authentication');
      expect(message).toContain('log in');
    });
  });

  describe('getRecommendedAction', () => {
    it('should recommend checking auth for auth errors', () => {
      const error = new AppError(
        'Auth failed',
        {
          category: ErrorCategory.AUTHENTICATION,
          severity: ErrorSeverity.HIGH,
          code: ErrorCodes.AUTH_ERROR,
        }
      );

      const action = ErrorRecovery.getRecommendedAction(error);

      expect(action).toContain('authentication');
    });

    it('should mention automatic retry for transient errors', () => {
      const error = new AppError(
        'Network error',
        {
          category: ErrorCategory.NETWORK,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.NETWORK_ERROR,
        }
      );

      const action = ErrorRecovery.getRecommendedAction(error);

      expect(action).toContain('temporary');
      expect(action).toContain('automatically');
    });

    it('should suggest contacting support for persistent errors', () => {
      const error = new AppError(
        'Unknown error',
        {
          category: ErrorCategory.UNKNOWN,
          severity: ErrorSeverity.MEDIUM,
          code: ErrorCodes.UNKNOWN_ERROR,
        }
      );

      const action = ErrorRecovery.getRecommendedAction(error);

      expect(action).toContain('support');
    });
  });
});
