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
