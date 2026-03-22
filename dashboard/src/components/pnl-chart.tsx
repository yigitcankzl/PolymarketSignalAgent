"use client";

import { motion } from "motion/react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface PnLPoint {
  trade_number: number;
  question: string;
  signal: string;
  pnl: number;
  cumulative_pnl: number;
}

interface PnLChartProps {
  data: PnLPoint[];
}

export function PnLChart({ data }: PnLChartProps) {
  if (!data.length) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500">
        No backtest data available.
      </div>
    );
  }

  const maxPnL = Math.max(...data.map((d) => d.cumulative_pnl));
  const minPnL = Math.min(...data.map((d) => d.cumulative_pnl));
  const isPositive = data[data.length - 1]?.cumulative_pnl >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6, duration: 0.5 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-5"
    >
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Cumulative P&L</h2>
        <p className="text-xs text-zinc-500 mt-1">
          Final: <span className={isPositive ? "text-green-400" : "text-red-400"}>
            {isPositive ? "+" : ""}{data[data.length - 1]?.cumulative_pnl.toFixed(4)}
          </span>
        </p>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <defs>
            <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="5%"
                stopColor={isPositive ? "#22c55e" : "#ef4444"}
                stopOpacity={0.3}
              />
              <stop
                offset="95%"
                stopColor={isPositive ? "#22c55e" : "#ef4444"}
                stopOpacity={0}
              />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="trade_number"
            stroke="#52525b"
            tick={{ fill: "#71717a", fontSize: 11 }}
            label={{ value: "Trade #", position: "insideBottom", offset: -2, fill: "#71717a", fontSize: 11 }}
          />
          <YAxis
            stroke="#52525b"
            tick={{ fill: "#71717a", fontSize: 11 }}
            domain={[Math.min(minPnL * 1.1, -0.1), Math.max(maxPnL * 1.1, 0.1)]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#a1a1aa" }}
            formatter={(value) => [Number(value).toFixed(4), "Cumulative P&L"]}
            labelFormatter={(label) => `Trade #${label}`}
          />
          <Area
            type="monotone"
            dataKey="cumulative_pnl"
            stroke={isPositive ? "#22c55e" : "#ef4444"}
            strokeWidth={2}
            fill="url(#pnlGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
