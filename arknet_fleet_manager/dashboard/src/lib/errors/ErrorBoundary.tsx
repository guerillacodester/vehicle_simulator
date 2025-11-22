// React error boundary for UI components
import React from 'react';
import { ErrorHandler, AppError } from './ErrorHandler';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  error: AppError | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { error: ErrorHandler.handle(error) };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    ErrorHandler.handle(error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong.</h2>
          <pre>{this.state.error.message}</pre>
          <pre>{this.state.error.code}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
