type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface ErrorContext {
  component?: string;
  action?: string;
  phase?: string;
  sessionId?: string;
  metadata?: Record<string, unknown>;
}

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context?: ErrorContext;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
}

const LOG_PREFIX = '[Sovereign]';
const ENABLE_VERBOSE = process.env.NODE_ENV === 'development';

const formatTimestamp = (): string => {
  const now = new Date();
  return `${now.toISOString().slice(11, 23)}`;
};

const formatContext = (context?: ErrorContext): string => {
  if (!context) return '';
  const parts: string[] = [];
  if (context.component) parts.push(`component=${context.component}`);
  if (context.action) parts.push(`action=${context.action}`);
  if (context.phase) parts.push(`phase=${context.phase}`);
  if (context.sessionId) parts.push(`session=${context.sessionId.slice(0, 8)}...`);
  return parts.length > 0 ? ` [${parts.join(' ')}]` : '';
};

const createLogEntry = (
  level: LogLevel,
  message: string,
  context?: ErrorContext,
  error?: Error
): LogEntry => ({
  timestamp: formatTimestamp(),
  level,
  message,
  context,
  error: error ? {
    name: error.name,
    message: error.message,
    stack: error.stack,
  } : undefined,
});

class ErrorLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 100;
  
  private log(level: LogLevel, message: string, context?: ErrorContext, error?: Error) {
    const entry = createLogEntry(level, message, context, error);
    
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }
    
    const contextStr = formatContext(context);
    const prefix = `${LOG_PREFIX} ${entry.timestamp}`;
    
    switch (level) {
      case 'debug':
        if (ENABLE_VERBOSE) {
          console.log(`${prefix} [DEBUG]${contextStr} ${message}`);
        }
        break;
      case 'info':
        console.log(`${prefix} [INFO]${contextStr} ${message}`);
        break;
      case 'warn':
        console.warn(`${prefix} [WARN]${contextStr} ${message}`);
        break;
      case 'error':
        console.error(`${prefix} [ERROR]${contextStr} ${message}`);
        if (error?.stack && ENABLE_VERBOSE) {
          console.error('Stack trace:', error.stack);
        }
        break;
    }
  }
  
  debug(message: string, context?: ErrorContext) {
    this.log('debug', message, context);
  }
  
  info(message: string, context?: ErrorContext) {
    this.log('info', message, context);
  }
  
  warn(message: string, context?: ErrorContext) {
    this.log('warn', message, context);
  }
  
  error(message: string, error?: Error | unknown, context?: ErrorContext) {
    const err = error instanceof Error ? error : new Error(String(error));
    this.log('error', message, context, err);
  }
  
  networkError(url: string, status?: number, message?: string, context?: ErrorContext) {
    this.log('error', `Network error: ${url} - Status ${status ?? 'N/A'} - ${message ?? 'Unknown error'}`, context);
  }
  
  streamError(event: string, data?: unknown, context?: ErrorContext) {
    this.log('error', `Stream error on event "${event}": ${JSON.stringify(data)}`, context);
  }
  
  bundleError(message: string, context?: ErrorContext) {
    this.log('error', `Bundle/Metro error: ${message}`, context);
  }
  
  getLogs(): LogEntry[] {
    return [...this.logs];
  }
  
  getRecentErrors(count = 10): LogEntry[] {
    return this.logs
      .filter(log => log.level === 'error')
      .slice(-count);
  }
  
  clear() {
    this.logs = [];
  }
  
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

export const logger = new ErrorLogger();

export const withErrorBoundary = <T extends (...args: unknown[]) => unknown>(
  fn: T,
  context: ErrorContext
): T => {
  return ((...args: unknown[]) => {
    try {
      const result = fn(...args);
      if (result instanceof Promise) {
        return result.catch((error: Error) => {
          logger.error(`Async error in ${context.action || 'unknown action'}`, error, context);
          throw error;
        });
      }
      return result;
    } catch (error) {
      logger.error(`Error in ${context.action || 'unknown action'}`, error, context);
      throw error;
    }
  }) as T;
};

export const logApiRequest = (
  method: string,
  url: string,
  context?: ErrorContext
) => {
  logger.debug(`API Request: ${method} ${url}`, context);
};

export const logApiResponse = (
  method: string,
  url: string,
  status: number,
  duration: number,
  context?: ErrorContext
) => {
  const level = status >= 400 ? 'error' : 'info';
  logger[level](`API Response: ${method} ${url} - ${status} (${duration}ms)`, context);
};

export const logStreamEvent = (
  eventType: string,
  data?: unknown,
  context?: ErrorContext
) => {
  logger.debug(`Stream event: ${eventType} - ${JSON.stringify(data)?.slice(0, 100)}...`, context);
};
