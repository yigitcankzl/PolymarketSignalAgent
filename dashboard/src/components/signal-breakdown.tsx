"use client";

import { getSignalBg } from "@/lib/utils";

interface Signal {
  signal: string;
}

interface SignalBreakdownProps {
  signals: Signal[];
}

const SIGNAL_ORDER = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"];

export function SignalBreakdown({ signals }: SignalBreakdownProps) {
  const counts: Record<string, number> = {};
  for (const s of signals) {
    counts[s.signal] = (counts[s.signal] || 0) + 1;
  }

  const total = signals.length || 1;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-white">Signal Breakdown</h2>
        <p className="text-xs text-zinc-500 mt-1">{signals.length} total signals</p>
      </div>
      <div className="space-y-3">
        {SIGNAL_ORDER.map((signal) => {
          const count = counts[signal] || 0;
          const pct = (count / total) * 100;
          return (
            <div key={signal}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${getSignalBg(signal)}`}>
                  {signal}
                </span>
                <span className="text-xs text-zinc-400 font-mono">
                  {count} ({pct.toFixed(0)}%)
                </span>
              </div>
              <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    signal.includes("BUY") ? "bg-green-500" :
                    signal.includes("SELL") ? "bg-red-500" :
                    "bg-zinc-600"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
