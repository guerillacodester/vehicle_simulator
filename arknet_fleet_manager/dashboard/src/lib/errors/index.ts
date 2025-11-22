/**
 * Central export for errors module
 */
export {
  AppError,
  NetworkError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  SystemError,
  ConnectionError,
  TimeoutError,
  ErrorCategory,
  ErrorSeverity,
} from './AppError';

export {
  ErrorHandler,
  initializeErrorHandler,
  getGlobalErrorHandler,
  handleError,
  type IErrorHandler,
  type ErrorContext,
} from './ErrorHandler';

export { ErrorCodes, type ErrorCode } from './ErrorCodes';

export {
  RetryStrategy,
  CircuitState,
  type RetryConfig,
} from './RetryStrategy';

export {
  ErrorRecovery,
  type RecoveryAction,
} from './ErrorRecovery';

export { ErrorBoundary } from './ErrorBoundary';
