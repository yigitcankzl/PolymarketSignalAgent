"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface Signal {
  market_id: string;
  question: string;
  edge: number;
  signal: string;
}

interface EdgeChartProps {
  signals: Signal[];
}

export function EdgeChart({ signals }: EdgeChartProps) {
  const actionable = signals
    .filter((s) => s.signal !== "HOLD")
    .sort((a, b) => b.edge - a.edge)
    .map((s) => ({
      name: s.question.length > 30 ? s.question.slice(0, 30) + "..." : s.question,
      edge: Number((s.edge * 100).toFixed(2)),
      signal: s.signal,
    }));

  if (!actionable.length) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500">
        No edge data available.
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Edge Distribution</h2>
        <p className="text-xs text-zinc-500 mt-1">LLM probability vs market odds (%)</p>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={actionable} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis
            dataKey="name"
            stroke="#52525b"
            tick={{ fill: "#71717a", fontSize: 9 }}
            interval={0}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            stroke="#52525b"
            tick={{ fill: "#71717a", fontSize: 11 }}
            label={{ value: "Edge %", angle: -90, position: "insideLeft", fill: "#71717a", fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            formatter={(value) => [`${Number(value).toFixed(2)}%`, "Edge"]}
          />
          <Bar dataKey="edge" radius={[4, 4, 0, 0]}>
            {actionable.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.edge >= 0 ? "#22c55e" : "#ef4444"}
                fillOpacity={0.7}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
