"use client";

import { cn, getSignalBg, formatPercent } from "@/lib/utils";

interface Signal {
  market_id: string;
  question: string;
  market_odds: number;
  llm_probability: number;
  edge: number;
  confidence: number;
  signal: string;
  score: number;
  reasoning: string;
  news_count: number;
}

interface SignalTableProps {
  signals: Signal[];
}

export function SignalTable({ signals }: SignalTableProps) {
  if (!signals.length) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500">
        No signals available. Run the pipeline to generate signals.
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-white">Active Signals</h2>
        <p className="text-xs text-zinc-500 mt-1">Ranked by score (edge x confidence)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-500 text-xs uppercase tracking-wider">
              <th className="text-left px-5 py-3 font-medium">Market</th>
              <th className="text-right px-3 py-3 font-medium">Odds</th>
              <th className="text-right px-3 py-3 font-medium">LLM</th>
              <th className="text-right px-3 py-3 font-medium">Edge</th>
              <th className="text-right px-3 py-3 font-medium">Conf</th>
              <th className="text-center px-3 py-3 font-medium">Signal</th>
              <th className="text-right px-5 py-3 font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((s, i) => (
              <tr
                key={s.market_id}
                className={cn(
                  "border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors",
                  i % 2 === 0 ? "bg-zinc-900" : "bg-zinc-900/50"
                )}
              >
                <td className="px-5 py-3">
                  <div className="max-w-xs">
                    <p className="text-zinc-200 text-sm truncate">{s.question}</p>
                    <p className="text-zinc-600 text-xs mt-0.5">{s.news_count} news articles</p>
                  </div>
                </td>
                <td className="text-right px-3 py-3 text-zinc-300 font-mono text-xs">
                  {formatPercent(s.market_odds)}
                </td>
                <td className="text-right px-3 py-3 text-zinc-300 font-mono text-xs">
                  {formatPercent(s.llm_probability)}
                </td>
                <td className={cn(
                  "text-right px-3 py-3 font-mono text-xs font-medium",
                  s.edge > 0 ? "text-green-400" : s.edge < 0 ? "text-red-400" : "text-zinc-400"
                )}>
                  {s.edge > 0 ? "+" : ""}{formatPercent(s.edge)}
                </td>
                <td className="text-right px-3 py-3 text-zinc-300 font-mono text-xs">
                  {formatPercent(s.confidence)}
                </td>
                <td className="text-center px-3 py-3">
                  <span className={cn(
                    "inline-block px-2.5 py-1 rounded-full text-xs font-medium border",
                    getSignalBg(s.signal)
                  )}>
                    {s.signal}
                  </span>
                </td>
                <td className="text-right px-5 py-3 text-zinc-200 font-mono text-xs font-medium">
                  {s.score.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
