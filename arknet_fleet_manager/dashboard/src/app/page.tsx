"use client";

import { useEffect, useState } from "react";
import ServiceManager from "@/providers/ServiceManager";

interface ServiceStatus {
  name: string;
  state: 'stopped' | 'starting' | 'running' | 'healthy' | 'unhealthy' | 'failed';
  port?: number;
  message?: string;
  pid?: number;
}

export default function Home() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatuses = async () => {
    const result = await ServiceManager.getAllServiceStatuses();
    if (result.success && result.statuses) {
      setStatuses(result.statuses);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      await fetchStatuses();
    };
    fetchData();

    // Auto-refresh every 2 seconds if enabled
    let intervalId: NodeJS.Timeout;
    if (autoRefresh) {
      intervalId = setInterval(fetchData, 2000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh]);

  // Subscribe to realtime events from ServiceManager (via launcher websocket)
  useEffect(() => {
    const onEvent = (status: ServiceStatus) => {
      setStatuses(prev => {
        const exists = prev.find(s => s.name === status.name);
        if (exists) {
          return prev.map(s => (s.name === status.name ? status : s));
        }
        return [...prev, status];
      });
    };

    ServiceManager.onEvent(onEvent);
    return () => {
      ServiceManager.offEvent(onEvent);
    };
  }, []);

  const handleStart = async (serviceName: string) => {
    setLoading(true);
    const result = await ServiceManager.startService(serviceName);
    if (result.success) {
      // Immediately update the UI with the new status
      if (result.status) {
        setStatuses(prev => prev.map(s => 
          s.name === serviceName ? result.status! : s
        ));
      }
    }
    await fetchStatuses();
    setLoading(false);
  };

  const handleStop = async (serviceName: string) => {
    setLoading(true);
    await ServiceManager.stopService(serviceName);
    await fetchStatuses();
    setLoading(false);
  };

  const getStateColor = (state: ServiceStatus['state']) => {
    switch (state) {
      case 'healthy':
        return 'text-green-500';
      case 'running':
        return 'text-blue-500';
      case 'starting':
        return 'text-yellow-500';
      case 'unhealthy':
      case 'failed':
        return 'text-red-500';
      case 'stopped':
      default:
        return 'text-gray-500';
    }
  };

  const getStateEmoji = (state: ServiceStatus['state']) => {
    switch (state) {
      case 'healthy':
        return '🟢';
      case 'running':
        return '🔵';
      case 'starting':
        return '🟡';
      case 'unhealthy':
      case 'failed':
        return '🔴';
      case 'stopped':
      default:
        return '⚪';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-50 font-sans dark:bg-black p-4">
      <div className="w-full max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">ArkNet Fleet Service Manager</h1>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4"
              />
              <span className="text-sm">Auto-refresh</span>
            </label>
            <button
              onClick={fetchStatuses}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={loading}
            >
              Refresh Now
            </button>
          </div>
        </div>

        {loading && <p className="text-center mb-4">Loading...</p>}

        <div className="space-y-3">
          {statuses.map((service) => (
            <div
              key={service.name}
              className="flex items-center justify-between p-4 border rounded-lg shadow-sm bg-white dark:bg-zinc-800"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{getStateEmoji(service.state)}</span>
                  <h2 className="text-lg font-medium capitalize">{service.name.replace('_', ' ')}</h2>
                </div>
                <div className="mt-1 text-sm space-y-1">
                  <p className={`font-semibold ${getStateColor(service.state)}`}>
                    Status: {service.state.toUpperCase()}
                  </p>
                  {service.port && (
                    <p className="text-gray-600 dark:text-gray-400">
                      Port: {service.port}
                    </p>
                  )}
                  {service.pid && (
                    <p className="text-gray-600 dark:text-gray-400">
                      PID: {service.pid}
                    </p>
                  )}
                  {service.message && (
                    <p className="text-gray-500 dark:text-gray-500 italic">
                      {service.message}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  className="px-4 py-2 text-sm text-white bg-green-500 rounded hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  onClick={() => handleStart(service.name)}
                  disabled={service.state === "healthy" || service.state === "starting" || loading}
                >
                  Start
                </button>
                <button
                  className="px-4 py-2 text-sm text-white bg-red-500 rounded hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  onClick={() => handleStop(service.name)}
                  disabled={service.state === "stopped" || loading}
                >
                  Stop
                </button>
              </div>
            </div>
          ))}
        </div>

        {statuses.length === 0 && !loading && (
          <div className="text-center p-8 border rounded-lg bg-white dark:bg-zinc-800">
            <p className="text-gray-500">No services found. Make sure the launcher is running on port 7000.</p>
          </div>
        )}
      </div>
    </div>
  );
}
