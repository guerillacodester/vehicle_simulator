// ErrorRecovery: Centralized error recovery strategies
// Provides specific recovery actions for different error types

import { ErrorCodes } from './ErrorCodes';
import { AppError } from './AppError';

export interface RecoveryAction {
  type: 'retry' | 'fallback' | 'refresh-auth' | 'user-action' | 'abort';
  message: string;
  canAutoRecover: boolean;
  delay?: number;
}

export class ErrorRecovery {
  // Get recovery action for a given error
  static getRecoveryAction(error: AppError | Error): RecoveryAction {
    if (error instanceof AppError) {
      return this.getRecoveryForAppError(error);
    }
    
    // Unknown error - conservative approach
    return {
      type: 'retry',
      message: 'An unexpected error occurred. Retrying connection...',
      canAutoRecover: true,
      delay: 5000,
    };
  }

  private static getRecoveryForAppError(error: AppError): RecoveryAction {
    switch (error.code) {
      // Network errors - retry with backoff
      case ErrorCodes.NETWORK_ERROR:
        return {
          type: 'retry',
          message: 'Network connection lost. Attempting to reconnect...',
          canAutoRecover: true,
          delay: 2000,
        };

      // Authentication errors - try token refresh first
      case ErrorCodes.TOKEN_EXPIRED:
        return {
          type: 'refresh-auth',
          message: 'Session expired. Refreshing authentication...',
          canAutoRecover: true,
          delay: 1000,
        };

      case ErrorCodes.AUTH_ERROR:
        return {
          type: 'user-action',
          message: 'Authentication failed. Please log in again.',
          canAutoRecover: false,
        };

      // Data errors - retry but log for investigation
      case ErrorCodes.DATA_PARSE_ERROR:
        return {
          type: 'retry',
          message: 'Invalid data received. Will continue attempting connection...',
          canAutoRecover: true,
          delay: 5000,
        };

      case ErrorCodes.DATA_VALIDATION_ERROR:
        return {
          type: 'retry',
          message: 'Data validation failed. Retrying...',
          canAutoRecover: true,
          delay: 3000,
        };

      // Server errors - use fallback if available
      case ErrorCodes.SERVER_ERROR:
        return {
          type: 'fallback',
          message: 'Server error. Attempting fallback connection method...',
          canAutoRecover: true,
          delay: 3000,
        };

      // Rate limiting - longer backoff
      case ErrorCodes.RATE_LIMIT_ERROR:
        return {
          type: 'retry',
          message: 'Rate limit exceeded. Waiting before retry...',
          canAutoRecover: true,
          delay: 10000,
        };

      // Client errors - likely permanent, but still retry
      case ErrorCodes.CLIENT_ERROR:
        return {
          type: 'retry',
          message: 'Client error occurred. Retrying with caution...',
          canAutoRecover: true,
          delay: 5000,
        };

      // Unknown error - conservative retry
      case ErrorCodes.UNKNOWN_ERROR:
      default:
        return {
          type: 'retry',
          message: 'Unexpected error. Retrying connection...',
          canAutoRecover: true,
          delay: 5000,
        };
    }
  }

  // Check if error is transient (temporary and worth retrying)
  static isTransientError(error: AppError | Error): boolean {
    if (!(error instanceof AppError)) {
      return true; // Assume transient if we don't know
    }

    const transientErrors: ErrorCodes[] = [
      ErrorCodes.NETWORK_ERROR,
      ErrorCodes.TOKEN_EXPIRED,
      ErrorCodes.SERVER_ERROR,
      ErrorCodes.RATE_LIMIT_ERROR,
    ];

    return transientErrors.includes(error.code as ErrorCodes);
  }

  // Check if error requires user intervention
  static requiresUserAction(error: AppError | Error): boolean {
    if (!(error instanceof AppError)) {
      return false;
    }

    const userActionErrors: ErrorCodes[] = [
      ErrorCodes.AUTH_ERROR,
    ];

    return userActionErrors.includes(error.code as ErrorCodes);
  }

  // Get user-friendly error message
  static getUserMessage(error: AppError | Error): string {
    const recovery = this.getRecoveryAction(error);
    return recovery.message;
  }

  // Get recommended action for UI display
  static getRecommendedAction(error: AppError | Error): string {
    if (this.requiresUserAction(error)) {
      return 'Please check your authentication and try again.';
    }

    if (this.isTransientError(error)) {
      return 'This issue is usually temporary. The connection will retry automatically.';
    }

    return 'If this problem persists, please contact support.';
  }
}
