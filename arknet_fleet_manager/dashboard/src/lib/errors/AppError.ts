/**
 * Error Categories for compartmentalization
 */
export enum ErrorCategory {
  NETWORK = 'NETWORK',           // Network/API errors
  VALIDATION = 'VALIDATION',     // Input validation errors
  AUTHENTICATION = 'AUTHENTICATION', // Auth errors
  AUTHORIZATION = 'AUTHORIZATION',   // Permission errors
  NOT_FOUND = 'NOT_FOUND',       // Resource not found
  CONFLICT = 'CONFLICT',         // Resource conflict
  BUSINESS_LOGIC = 'BUSINESS_LOGIC', // Business rule violations
  SYSTEM = 'SYSTEM',             // System/infrastructure errors
  EXTERNAL = 'EXTERNAL',         // Third-party service errors
  UNKNOWN = 'UNKNOWN',           // Unknown errors
}

/**
 * Error Severity Levels
 */
export enum ErrorSeverity {
  LOW = 'LOW',           // Minor issue, doesn't affect functionality
  MEDIUM = 'MEDIUM',     // Affects some functionality
  HIGH = 'HIGH',         // Affects major functionality
  CRITICAL = 'CRITICAL', // System-breaking error
}

/**
 * Base application error with structured metadata
 */
export class AppError extends Error {
  public readonly category: ErrorCategory;
  public readonly severity: ErrorSeverity;
  public readonly code: string;
  public readonly timestamp: Date;
  public readonly metadata: Record<string, unknown>;
  public readonly recoverable: boolean;
  public readonly userMessage: string;
  public readonly component?: string;

  constructor(
    message: string,
    options: {
      category: ErrorCategory;
      severity: ErrorSeverity;
      code: string;
      metadata?: Record<string, unknown>;
      recoverable?: boolean;
      userMessage?: string;
      component?: string;
      cause?: Error;
    }
  ) {
    super(message);
    this.name = 'AppError';
    this.category = options.category;
    this.severity = options.severity;
    this.code = options.code;
    this.metadata = options.metadata || {};
    this.recoverable = options.recoverable ?? true;
    this.userMessage = options.userMessage || message;
    this.component = options.component;
    this.timestamp = new Date();

    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }

    // Store cause if provided
    if (options.cause) {
      this.cause = options.cause;
    }
  }

  /**
   * Convert error to JSON for logging/transmission
   */
  toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      message: this.message,
      userMessage: this.userMessage,
      category: this.category,
      severity: this.severity,
      code: this.code,
      timestamp: this.timestamp.toISOString(),
      metadata: this.metadata,
      recoverable: this.recoverable,
      component: this.component,
      stack: this.stack,
      cause: this.cause instanceof Error ? {
        name: this.cause.name,
        message: this.cause.message,
        stack: this.cause.stack,
      } : undefined,
    };
  }
}

/**
 * Network/API Error
 */
export class NetworkError extends AppError {
  constructor(
    message: string,
    options: {
      code?: string;
      statusCode?: number;
      url?: string;
      method?: string;
      metadata?: Record<string, unknown>;
      cause?: Error;
    } = {}
  ) {
    super(message, {
      category: ErrorCategory.NETWORK,
      severity: ErrorSeverity.MEDIUM,
      code: options.code || `NETWORK_${options.statusCode || 'ERROR'}`,
      metadata: {
        statusCode: options.statusCode,
        url: options.url,
        method: options.method,
        ...options.metadata,
      },
      userMessage: 'Network error occurred. Please check your connection.',
      recoverable: true,
      cause: options.cause,
    });
    this.name = 'NetworkError';
  }
}

/**
 * Validation Error
 */
export class ValidationError extends AppError {
  public readonly field?: string;
  public readonly value?: unknown;

  constructor(
    message: string,
    options: {
      field?: string;
      value?: unknown;
      code?: string;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    super(message, {
      category: ErrorCategory.VALIDATION,
      severity: ErrorSeverity.LOW,
      code: options.code || 'VALIDATION_ERROR',
      metadata: {
        field: options.field,
        value: options.value,
        ...options.metadata,
      },
      userMessage: message,
      recoverable: true,
    });
    this.name = 'ValidationError';
    this.field = options.field;
    this.value = options.value;
  }
}

/**
 * Authentication Error
 */
export class AuthenticationError extends AppError {
  constructor(
    message: string = 'Authentication required',
    options: {
      code?: string;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    super(message, {
      category: ErrorCategory.AUTHENTICATION,
      severity: ErrorSeverity.HIGH,
      code: options.code || 'AUTH_REQUIRED',
      metadata: options.metadata,
      userMessage: 'Please log in to continue.',
      recoverable: true,
    });
    this.name = 'AuthenticationError';
  }
}

/**
 * Authorization Error
 */
export class AuthorizationError extends AppError {
  constructor(
    message: string = 'Access denied',
    options: {
      resource?: string;
      action?: string;
      code?: string;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    super(message, {
      category: ErrorCategory.AUTHORIZATION,
      severity: ErrorSeverity.HIGH,
      code: options.code || 'ACCESS_DENIED',
      metadata: {
        resource: options.resource,
        action: options.action,
        ...options.metadata,
      },
      userMessage: 'You do not have permission to perform this action.',
      recoverable: false,
    });
    this.name = 'AuthorizationError';
  }
}

/**
 * Not Found Error
 */
export class NotFoundError extends AppError {
  constructor(
    resource: string,
    id?: string,
    options: {
      code?: string;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    super(`${resource} not found${id ? `: ${id}` : ''}`, {
      category: ErrorCategory.NOT_FOUND,
      severity: ErrorSeverity.MEDIUM,
      code: options.code || 'NOT_FOUND',
      metadata: {
        resource,
        id,
        ...options.metadata,
      },
      userMessage: `The requested ${resource.toLowerCase()} could not be found.`,
      recoverable: false,
    });
    this.name = 'NotFoundError';
  }
}

/**
 * System Error
 */
export class SystemError extends AppError {
  constructor(
    message: string,
    options: {
      code?: string;
      metadata?: Record<string, unknown>;
      cause?: Error;
      component?: string;
    } = {}
  ) {
    super(message, {
      category: ErrorCategory.SYSTEM,
      severity: ErrorSeverity.CRITICAL,
      code: options.code || 'SYSTEM_ERROR',
      metadata: options.metadata,
      userMessage: 'A system error occurred. Please try again later.',
      recoverable: false,
      component: options.component,
      cause: options.cause,
    });
    this.name = 'SystemError';
  }
}

/**
 * Connection Error (specific type of network error)
 */
export class ConnectionError extends NetworkError {
  constructor(
    message: string = 'Connection failed',
    options: {
      url?: string;
      cause?: Error;
      metadata?: Record<string, unknown>;
    } = {}
  ) {
    super(message, {
      code: 'CONNECTION_FAILED',
      url: options.url,
      metadata: options.metadata,
      cause: options.cause,
    });
    this.name = 'ConnectionError';
  }
}

/**
 * Timeout Error
 */
export class TimeoutError extends NetworkError {
  constructor(
    message: string = 'Request timeout',
    options: {
      timeout?: number;
      url?: string;
      cause?: Error;
    } = {}
  ) {
    super(message, {
      code: 'TIMEOUT',
      url: options.url,
      metadata: { timeout: options.timeout },
      cause: options.cause,
    });
    this.name = 'TimeoutError';
  }
}
