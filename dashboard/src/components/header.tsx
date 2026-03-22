"use client";

import { useState, useEffect, useCallback } from "react";
import { Activity, BarChart3, TrendingUp, RefreshCw } from "lucide-react";

interface HeaderProps {
  marketCount: number;
  lastRun: string;
  onRefresh: () => void;
  refreshInterval: number;
}

export function Header({ marketCount, lastRun, onRefresh, refreshInterval }: HeaderProps) {
  const [countdown, setCountdown] = useState(refreshInterval);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
    setCountdown(refreshInterval);
  }, [onRefresh, refreshInterval]);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          handleRefresh();
          return refreshInterval;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [refreshInterval, handleRefresh]);

  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-green-500/20 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">Polymarket Signal Agent</h1>
            <p className="text-xs text-zinc-500">
              AI-Powered Signals &middot; via{" "}
              <a href="https://synthesis.trade" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300">
                Synthesis.trade
              </a>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-5 text-sm">
          <div className="flex items-center gap-2 text-zinc-400">
            <BarChart3 className="w-4 h-4" />
            <span>{marketCount} markets</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-400">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
            </span>
            <span className="text-green-400 text-xs font-medium">Live</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-500 text-xs">
            <Activity className="w-3.5 h-3.5" />
            <span>{lastRun || "—"}</span>
          </div>
          <button
            onClick={handleRefresh}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-all text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>{countdown}s</span>
          </button>
        </div>
      </div>
    </header>
  );
}
