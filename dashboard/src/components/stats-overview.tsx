"use client";

import { TrendingUp, Target, Gauge, BarChart3 } from "lucide-react";
import { formatPercent } from "@/lib/utils";

interface Metrics {
  total_signals: number;
  hit_rate: number;
  avg_edge: number;
  sharpe_ratio: number;
  total_pnl: number;
}

interface StatsOverviewProps {
  metrics: Metrics | null;
  signalCount: number;
}

export function StatsOverview({ metrics, signalCount }: StatsOverviewProps) {
  const stats = [
    {
      label: "Total Signals",
      value: signalCount.toString(),
      icon: BarChart3,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Hit Rate",
      value: metrics ? formatPercent(metrics.hit_rate) : "—",
      icon: Target,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Avg Edge",
      value: metrics ? formatPercent(metrics.avg_edge) : "—",
      icon: TrendingUp,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Sharpe Ratio",
      value: metrics ? metrics.sharpe_ratio.toFixed(2) : "—",
      icon: Gauge,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-8 h-8 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <span className="text-xs text-zinc-500 uppercase tracking-wider">{stat.label}</span>
          </div>
          <p className="text-2xl font-bold text-white">{stat.value}</p>
        </div>
      ))}
    </div>
  );
}
