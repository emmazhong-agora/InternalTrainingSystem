/**
 * Debug Logger - Captures console logs for debugging
 */

export interface LogEntry {
  timestamp: Date;
  level: 'log' | 'info' | 'warn' | 'error';
  category: string;
  message: string;
  data?: any;
}

class DebugLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 500; // Keep last 500 logs
  private enabled = false;

  constructor() {
    if (import.meta.env.DEV) {
      this.enable();
    }
  }

  enable() {
    this.enabled = true;
    this.interceptConsole();
  }

  disable() {
    this.enabled = false;
  }

  private interceptConsole() {
    const originalLog = console.log;
    const originalInfo = console.info;
    const originalWarn = console.warn;
    const originalError = console.error;

    console.log = (...args: any[]) => {
      this.captureLog('log', args);
      originalLog.apply(console, args);
    };

    console.info = (...args: any[]) => {
      this.captureLog('info', args);
      originalInfo.apply(console, args);
    };

    console.warn = (...args: any[]) => {
      this.captureLog('warn', args);
      originalWarn.apply(console, args);
    };

    console.error = (...args: any[]) => {
      this.captureLog('error', args);
      originalError.apply(console, args);
    };
  }

  private captureLog(level: LogEntry['level'], args: any[]) {
    if (!this.enabled) return;

    const firstArg = args[0];
    let category = 'General';
    let message = '';

    // Extract category from log messages
    if (typeof firstArg === 'string') {
      const match = firstArg.match(/^\[([^\]]+)\]/);
      if (match) {
        category = match[1];
        message = firstArg;
      } else {
        message = firstArg;
      }
    } else {
      message = String(firstArg);
    }

    const entry: LogEntry = {
      timestamp: new Date(),
      level,
      category,
      message,
      data: args.length > 1 ? args.slice(1) : undefined,
    };

    this.logs.push(entry);

    // Keep only last N logs
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }
  }

  getLogs(category?: string): LogEntry[] {
    if (category) {
      return this.logs.filter(log => log.category === category);
    }
    return [...this.logs];
  }

  getLogsByLevel(level: LogEntry['level']): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  clear() {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  downloadLogs(filename = 'debug-logs.json') {
    const data = this.exportLogs();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  getLogSummary(): {
    total: number;
    byLevel: Record<string, number>;
    byCategory: Record<string, number>;
    errors: LogEntry[];
  } {
    const byLevel: Record<string, number> = {};
    const byCategory: Record<string, number> = {};

    this.logs.forEach(log => {
      byLevel[log.level] = (byLevel[log.level] || 0) + 1;
      byCategory[log.category] = (byCategory[log.category] || 0) + 1;
    });

    return {
      total: this.logs.length,
      byLevel,
      byCategory,
      errors: this.getLogsByLevel('error'),
    };
  }
}

export const debugLogger = new DebugLogger();
