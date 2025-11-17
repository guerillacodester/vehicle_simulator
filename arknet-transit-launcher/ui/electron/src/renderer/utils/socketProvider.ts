// Reusable Socket.IO provider with reconnect/retry logic for Electron/Next.js
import { io, Socket } from 'socket.io-client';

export interface SocketProviderOptions {
  url: string;
  token?: string;
  maxRetries?: number;
  backoffBase?: number;
  backoffMax?: number;
}

class SocketProvider {
  private socket: Socket | null = null;
  private retries = 0;
  private options: SocketProviderOptions | null = null;

  connect(options: SocketProviderOptions) {
    this.options = options;
    this.retries = 0;
    this._connect();
  }

  private _connect() {
    if (!this.options) throw new Error('No options provided');
    const { url, token } = this.options;
    this.socket = io(url, {
      auth: { token },
      transports: ['websocket'],
      reconnection: false // We'll handle reconnection manually
    });
    this._setupListeners();
  }

  private _setupListeners() {
    if (!this.socket) return;
    this.socket.on('connect', () => {
      this.retries = 0;
      console.log('Socket.IO connected');
    });
    this.socket.on('disconnect', (reason: string) => {
      console.warn('Socket.IO disconnected:', reason);
      this._retryConnect();
    });
    this.socket.on('connect_error', (err: any) => {
      console.error('Socket.IO connect error:', err);
      this._retryConnect();
    });
  }

  private _retryConnect() {
    if (!this.options) return;
    const maxRetries = this.options.maxRetries ?? 5;
    if (this.retries >= maxRetries) {
      console.error('Max Socket.IO retries reached');
      return;
    }
    this.retries++;
    const base = this.options.backoffBase ?? 1000;
    const max = this.options.backoffMax ?? 10000;
    const delay = Math.min(base * Math.pow(2, this.retries), max);
    setTimeout(() => {
      console.log(`Retrying Socket.IO connection (attempt ${this.retries})...`);
      this._connect();
    }, delay);
  }

  on(event: string, handler: (...args: any[]) => void) {
    this.socket?.on(event, handler);
  }

  emit(event: string, ...args: any[]) {
    this.socket?.emit(event, ...args);
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
  }
}

const socketProvider = new SocketProvider();
export default socketProvider;
