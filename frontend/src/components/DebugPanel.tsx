/**
 * Debug Panel - Shows real-time logs and system status
 */
import React, { useState, useEffect } from 'react';
import { debugLogger, type LogEntry } from '../utils/debugLogger';

interface DebugPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({ isOpen, onClose }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<string>('');
  const [levelFilter, setLevelFilter] = useState<string>('all');

  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      setLogs(debugLogger.getLogs());
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  const summary = debugLogger.getLogSummary();

  const filteredLogs = logs.filter(log => {
    const matchesText = !filter ||
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.category.toLowerCase().includes(filter.toLowerCase());

    const matchesLevel = levelFilter === 'all' || log.level === levelFilter;

    return matchesText && matchesLevel;
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'text-red-600';
      case 'warn': return 'text-yellow-600';
      case 'info': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Debug Console</h2>
            <p className="text-sm text-gray-600">
              {summary.total} logs | {summary.errors.length} errors
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => debugLogger.downloadLogs()}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Download Logs
            </button>
            <button
              onClick={() => {
                debugLogger.clear();
                setLogs([]);
              }}
              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Clear
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
            >
              Close
            </button>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="p-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Errors:</span>
              <span className="ml-2 font-semibold text-red-600">
                {summary.byLevel.error || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Warnings:</span>
              <span className="ml-2 font-semibold text-yellow-600">
                {summary.byLevel.warn || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Info:</span>
              <span className="ml-2 font-semibold text-blue-600">
                {summary.byLevel.info || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Logs:</span>
              <span className="ml-2 font-semibold text-gray-600">
                {summary.byLevel.log || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 border-b border-gray-200 flex gap-4">
          <input
            type="text"
            placeholder="Filter logs..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded text-sm"
          />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded text-sm"
          >
            <option value="all">All Levels</option>
            <option value="error">Errors</option>
            <option value="warn">Warnings</option>
            <option value="info">Info</option>
            <option value="log">Logs</option>
          </select>
        </div>

        {/* Logs */}
        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs bg-gray-900 text-green-400">
          {filteredLogs.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No logs {filter || levelFilter !== 'all' ? 'matching filter' : 'yet'}
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div key={index} className="mb-2 border-b border-gray-800 pb-2">
                <div className="flex items-start gap-2">
                  <span className="text-gray-500">
                    {log.timestamp.toLocaleTimeString()}
                  </span>
                  <span className={`font-semibold ${getLevelColor(log.level)}`}>
                    [{log.level.toUpperCase()}]
                  </span>
                  <span className="text-cyan-400">[{log.category}]</span>
                  <span className="flex-1">{log.message}</span>
                </div>
                {log.data && (
                  <div className="ml-24 mt-1 text-gray-400">
                    {JSON.stringify(log.data, null, 2)}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Category Summary */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-600">
            <strong>Categories:</strong>{' '}
            {Object.entries(summary.byCategory).map(([cat, count], i) => (
              <span key={cat}>
                {i > 0 && ' | '}
                {cat}: {count}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
