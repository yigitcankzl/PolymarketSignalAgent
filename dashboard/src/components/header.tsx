"use client";

import { Activity, BarChart3, TrendingUp } from "lucide-react";

interface HeaderProps {
  marketCount: number;
  lastRun: string;
}

export function Header({ marketCount, lastRun }: HeaderProps) {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-green-500/20 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-green-400" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-white">Polymarket Signal Agent</h1>
            <p className="text-xs text-zinc-500">AI-Powered Prediction Market Signals</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2 text-zinc-400">
            <BarChart3 className="w-4 h-4" />
            <span>{marketCount} markets</span>
          </div>
          <div className="flex items-center gap-2 text-zinc-400">
            <Activity className="w-4 h-4 text-green-400" />
            <span>{lastRun || "Not run yet"}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
