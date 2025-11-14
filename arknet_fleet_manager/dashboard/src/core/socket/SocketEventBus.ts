// Agnostic Event Bus for Socket.IO events following SOLID principles
import { ISocketEventBus, ISocketEventHandler, ISocketEventFilter } from '../../interfaces/socket';

export class SocketEventBus<T = unknown> implements ISocketEventBus<T> {
  private subscriptions: Map<string, ISocketEventHandler<T>[]> = new Map();
  private filters: Map<string, ISocketEventFilter<T>[]> = new Map();

  publish(event: string, data: T): void {
    const handlers = this.subscriptions.get(event);
    const eventFilters = this.filters.get(event);

    if (!handlers || handlers.length === 0) {
      return;
    }

    // Apply filters if any exist for this event
    const filteredHandlers = eventFilters && eventFilters.length > 0
      ? handlers.filter(h => eventFilters.every(filter => filter.matches(event, data)))
      : handlers;

    // Notify all matching handlers
    filteredHandlers.forEach(handler => {
      try {
        if (handler.canHandle(event, data)) {
          handler.handle(event, data);
        }
      } catch (error) {
        console.error(`[SocketEventBus] Error in event handler for '${event}':`, error);
      }
    });
  }

  subscribe(event: string, handler: ISocketEventHandler<T>): () => void {
    if (!this.subscriptions.has(event)) {
      this.subscriptions.set(event, []);
    }

    const handlers = this.subscriptions.get(event)!;
    if (!handlers.includes(handler)) {
      handlers.push(handler);
    }

    // Return unsubscribe function for convenience
    return () => this.unsubscribe(event, handler);
  }

  unsubscribe(event: string, handler?: ISocketEventHandler<T>): void {
    const handlers = this.subscriptions.get(event);
    if (!handlers) return;

    if (handler) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      // Remove all handlers for this event
      handlers.length = 0;
    }

    // Clean up empty subscription arrays
    if (handlers.length === 0) {
      this.subscriptions.delete(event);
    }
  }

  addFilter(event: string, filter: ISocketEventFilter<T>): () => void {
    if (!this.filters.has(event)) {
      this.filters.set(event, []);
    }

    const eventFilters = this.filters.get(event)!;
    if (!eventFilters.includes(filter)) {
      eventFilters.push(filter);
    }

    // Return remove function for convenience
    return () => this.removeFilter(event, filter);
  }

  removeFilter(event: string, filter?: ISocketEventFilter<T>): void {
    const eventFilters = this.filters.get(event);
    if (!eventFilters) return;

    if (filter) {
      const index = eventFilters.indexOf(filter);
      if (index > -1) {
        eventFilters.splice(index, 1);
      }
    } else {
      // Remove all filters for this event
      eventFilters.length = 0;
    }

    // Clean up empty filter arrays
    if (eventFilters.length === 0) {
      this.filters.delete(event);
    }
  }

  clear(): void {
    this.subscriptions.clear();
    this.filters.clear();
  }

  getSubscriptionCount(event?: string): number {
    if (event) {
      return this.subscriptions.get(event)?.length || 0;
    }
    return Array.from(this.subscriptions.values()).reduce((total, handlers) => total + handlers.length, 0);
  }

  getSubscribedEvents(): string[] {
    return Array.from(this.subscriptions.keys());
  }
}

// Concrete event handler implementation
export abstract class BaseSocketEventHandler<T = unknown> implements ISocketEventHandler<T> {
  abstract handle(event: string, data: T): void;

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  canHandle(event: string, data: T): boolean {
    // Default implementation - can handle any event
    // Subclasses can override for specific filtering
    return true;
  }
}

// Filtered event handler that only handles specific events
export class FilteredSocketEventHandler<T = unknown> extends BaseSocketEventHandler<T> {
  constructor(
    private filter: ISocketEventFilter<T>,
    private handler: (event: string, data: T) => void
  ) {
    super();
  }

  handle(event: string, data: T): void {
    this.handler(event, data);
  }

  canHandle(event: string, data: T): boolean {
    return this.filter.matches(event, data);
  }
}

// Utility function to create event filters
export class SocketEventFilters {
  static byProperty<T = unknown>(property: keyof T, value: unknown): ISocketEventFilter<T> {
    return {
      matches: (_event: string, data: T) => {
        return data && typeof data === 'object' && (data as Record<string, unknown>)[property as string] === value;
      }
    };
  }

  static byEventName(eventName: string): ISocketEventFilter {
    return {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      matches: (event: string, _data: unknown) => event === eventName
    };
  }

  static byPredicate<T = unknown>(predicate: (event: string, data: T) => boolean): ISocketEventFilter<T> {
    return {
      matches: predicate
    };
  }

  static combine<T = unknown>(...filters: ISocketEventFilter<T>[]): ISocketEventFilter<T> {
    return {
      matches: (event: string, data: T) => {
        return filters.every(filter => filter.matches(event, data));
      }
    };
  }
}