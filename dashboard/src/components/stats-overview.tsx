"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { TrendingUp, Target, Gauge, BarChart3 } from "lucide-react";

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

function AnimatedNumber({ value, format = "number", duration = 1.2 }: {
  value: number;
  format?: "number" | "percent" | "decimal";
  duration?: number;
}) {
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    const start = 0;
    const end = value;
    const startTime = Date.now();
    const ms = duration * 1000;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / ms, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = start + (end - start) * eased;

      if (format === "percent") {
        setDisplay(`${(current * 100).toFixed(1)}%`);
      } else if (format === "decimal") {
        setDisplay(current.toFixed(2));
      } else {
        setDisplay(Math.round(current).toString());
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }, [value, format, duration]);

  return <>{display}</>;
}

export function StatsOverview({ metrics, signalCount }: StatsOverviewProps) {
  const stats = [
    {
      label: "Total Signals",
      numValue: signalCount,
      format: "number" as const,
      icon: BarChart3,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Hit Rate",
      numValue: metrics?.hit_rate ?? 0,
      format: "percent" as const,
      icon: Target,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Avg Edge",
      numValue: metrics?.avg_edge ?? 0,
      format: "percent" as const,
      icon: TrendingUp,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Sharpe Ratio",
      numValue: metrics?.sharpe_ratio ?? 0,
      format: "decimal" as const,
      icon: Gauge,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <motion.div
          key={stat.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1, duration: 0.5 }}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
        >
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-8 h-8 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <span className="text-xs text-zinc-500 uppercase tracking-wider">{stat.label}</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {metrics || stat.label === "Total Signals" ? (
              <AnimatedNumber value={stat.numValue} format={stat.format} />
            ) : "—"}
          </p>
        </motion.div>
      ))}
    </div>
  );
}
