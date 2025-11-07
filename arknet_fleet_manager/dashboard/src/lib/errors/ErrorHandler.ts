import { AppError, ErrorSeverity } from './AppError';
import { Logger } from '../logger/Logger';

/**
 * Error handler interface
 */
export interface IErrorHandler {
  handle(error: Error | AppError | unknown, context?: ErrorContext): void;
  canHandle?(error: Error | AppError | unknown): boolean;
}

/**
 * Error context for additional information
 */
export interface ErrorContext {
  component?: string;
  action?: string;
  metadata?: Record<string, unknown>;
  user?: {
    id?: string;
    session?: string;
  };
}

/**
 * Centralized error handler
 */
export class ErrorHandler implements IErrorHandler {
  private logger: Logger;
  private handlers: IErrorHandler[] = [];

  constructor(logger: Logger) {
    this.logger = logger;
  }

  /**
   * Register a custom error handler
   */
  registerHandler(handler: IErrorHandler): void {
    this.handlers.push(handler);
  }

  /**
   * Handle an error
   */
  handle(error: Error | AppError | unknown, context?: ErrorContext): void {
    // Try custom handlers first
    for (const handler of this.handlers) {
      if (handler.canHandle && handler.canHandle(error)) {
        try {
          handler.handle(error, context);
          return;
        } catch (handlerError) {
          this.logger.error('Error in custom error handler', handlerError, {
            action: 'handle',
            metadata: { originalError: String(error) }
          });
        }
      }
    }

    // Default handling
    if (error instanceof AppError) {
      this.handleAppError(error, context);
    } else if (error instanceof Error) {
      this.handleStandardError(error, context);
    } else {
      this.handleUnknownError(error, context);
    }
  }

  /**
   * Handle AppError instances
   */
  private handleAppError(error: AppError, context?: ErrorContext): void {
    const logMetadata = {
      action: context?.action,
      metadata: {
        ...error.metadata,
        ...context?.metadata,
        category: error.category,
        severity: error.severity,
        code: error.code,
        recoverable: error.recoverable,
        userMessage: error.userMessage,
      },
      user: context?.user,
    };

    // Log based on severity
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        this.logger.critical(error.message, logMetadata);
        break;
      case ErrorSeverity.HIGH:
        this.logger.error(error.message, error, logMetadata);
        break;
      case ErrorSeverity.MEDIUM:
        this.logger.warn(error.message, logMetadata);
        break;
      case ErrorSeverity.LOW:
        this.logger.info(error.message, logMetadata);
        break;
    }
  }

  /**
   * Handle standard Error instances
   */
  private handleStandardError(error: Error, context?: ErrorContext): void {
    this.logger.error(error.message, error, {
      action: context?.action,
      metadata: context?.metadata,
      user: context?.user,
    });
  }

  /**
   * Handle unknown errors
   */
  private handleUnknownError(error: unknown, context?: ErrorContext): void {
    this.logger.error('Unknown error occurred', new Error(String(error)), {
      action: context?.action,
      metadata: {
        ...context?.metadata,
        originalError: String(error),
      },
      user: context?.user,
    });
  }
}

/**
 * Global error handler instance (singleton)
 */
let globalErrorHandler: ErrorHandler | null = null;

/**
 * Initialize global error handler
 */
export function initializeErrorHandler(logger: Logger): ErrorHandler {
  if (!globalErrorHandler) {
    globalErrorHandler = new ErrorHandler(logger);

    // Set up global error handlers
    if (typeof window !== 'undefined') {
      // Handle unhandled promise rejections
      window.addEventListener('unhandledrejection', (event) => {
        globalErrorHandler?.handle(event.reason, {
          component: 'Global',
          action: 'unhandledRejection',
        });
        event.preventDefault();
      });

      // Handle uncaught errors
      window.addEventListener('error', (event) => {
        globalErrorHandler?.handle(event.error || event.message, {
          component: 'Global',
          action: 'uncaughtError',
          metadata: {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
          },
        });
        event.preventDefault();
      });
    }
  }
  return globalErrorHandler;
}

/**
 * Get global error handler
 */
export function getGlobalErrorHandler(): ErrorHandler {
  if (!globalErrorHandler) {
    throw new Error('Error handler not initialized. Call initializeErrorHandler first.');
  }
  return globalErrorHandler;
}

/**
 * Convenience function to handle errors
 */
export function handleError(error: Error | AppError | unknown, context?: ErrorContext): void {
  getGlobalErrorHandler().handle(error, context);
}
