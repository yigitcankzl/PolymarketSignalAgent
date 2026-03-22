"use client";

import { motion } from "motion/react";
import { formatPercent, formatPnL } from "@/lib/utils";
import { CheckCircle, XCircle, TrendingUp, TrendingDown } from "lucide-react";

interface Metrics {
  total_signals: number;
  correct_signals: number;
  hit_rate: number;
  total_pnl: number;
  avg_pnl: number;
  avg_edge: number;
  sharpe_ratio: number;
  max_drawdown: number;
  profit_factor: number;
  win_count: number;
  loss_count: number;
  best_trade: number;
  worst_trade: number;
  win_rate_by_signal: Record<string, number>;
}

interface BacktestPanelProps {
  metrics: Metrics | null;
}

export function BacktestPanel({ metrics }: BacktestPanelProps) {
  if (!metrics) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-center text-zinc-500">
        No backtest results. Run pipeline with --backtest flag.
      </div>
    );
  }

  const rows = [
    { label: "Total Trades", value: metrics.total_signals.toString() },
    { label: "Win / Loss", value: `${metrics.win_count} / ${metrics.loss_count}` },
    { label: "Hit Rate", value: formatPercent(metrics.hit_rate), highlight: metrics.hit_rate > 0.5 },
    { label: "Total P&L", value: formatPnL(metrics.total_pnl), highlight: metrics.total_pnl > 0 },
    { label: "Avg P&L", value: formatPnL(metrics.avg_pnl) },
    { label: "Sharpe Ratio", value: metrics.sharpe_ratio.toFixed(2), highlight: metrics.sharpe_ratio > 1 },
    { label: "Max Drawdown", value: metrics.max_drawdown.toFixed(4) },
    { label: "Profit Factor", value: metrics.profit_factor.toFixed(2), highlight: metrics.profit_factor > 1 },
    { label: "Best Trade", value: formatPnL(metrics.best_trade) },
    { label: "Worst Trade", value: formatPnL(metrics.worst_trade) },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5, duration: 0.5 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-white">Backtest Results</h2>
          <p className="text-xs text-zinc-500 mt-1">Historical performance metrics</p>
        </div>
        {metrics.total_pnl >= 0 ? (
          <TrendingUp className="w-5 h-5 text-green-400" />
        ) : (
          <TrendingDown className="w-5 h-5 text-red-400" />
        )}
      </div>
      <div className="divide-y divide-zinc-800/50">
        {rows.map((row) => (
          <div key={row.label} className="flex items-center justify-between px-5 py-2.5">
            <span className="text-xs text-zinc-500">{row.label}</span>
            <span className={`text-sm font-mono font-medium ${
              row.highlight !== undefined
                ? row.highlight ? "text-green-400" : "text-red-400"
                : "text-zinc-300"
            }`}>
              {row.value}
            </span>
          </div>
        ))}
      </div>

      {Object.keys(metrics.win_rate_by_signal).length > 0 && (
        <>
          <div className="px-5 py-3 border-t border-zinc-800">
            <p className="text-xs text-zinc-500 uppercase tracking-wider">Win Rate by Signal</p>
          </div>
          <div className="divide-y divide-zinc-800/50">
            {Object.entries(metrics.win_rate_by_signal).map(([signal, rate]) => (
              <div key={signal} className="flex items-center justify-between px-5 py-2">
                <span className="text-xs text-zinc-400">{signal}</span>
                <div className="flex items-center gap-2">
                  {rate > 0.5 ? (
                    <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                  ) : (
                    <XCircle className="w-3.5 h-3.5 text-red-400" />
                  )}
                  <span className={`text-xs font-mono ${rate > 0.5 ? "text-green-400" : "text-red-400"}`}>
                    {formatPercent(rate)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </motion.div>
  );
}
