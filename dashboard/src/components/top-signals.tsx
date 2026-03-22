"use client";

import { cn, getSignalBg, formatPercent } from "@/lib/utils";
import { Zap } from "lucide-react";

interface Signal {
  market_id: string;
  question: string;
  edge: number;
  confidence: number;
  signal: string;
  score: number;
  reasoning: string;
}

interface TopSignalsProps {
  signals: Signal[];
}

export function TopSignals({ signals }: TopSignalsProps) {
  const top = signals.filter((s) => s.signal !== "HOLD").slice(0, 5);

  if (!top.length) {
    return null;
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Zap className="w-4 h-4 text-amber-400" />
        <h2 className="text-sm font-semibold text-white">Top Signals</h2>
      </div>
      <div className="space-y-3">
        {top.map((s) => (
          <div
            key={s.market_id}
            className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700/50"
          >
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <p className="text-xs text-zinc-300 leading-relaxed flex-1">
                {s.question}
              </p>
              <span className={cn(
                "text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0",
                getSignalBg(s.signal)
              )}>
                {s.signal}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-zinc-500">
              <span>Edge: <span className={s.edge > 0 ? "text-green-400" : "text-red-400"}>
                {s.edge > 0 ? "+" : ""}{formatPercent(s.edge)}
              </span></span>
              <span>Conf: {formatPercent(s.confidence)}</span>
              <span>Score: {s.score.toFixed(4)}</span>
            </div>
            <p className="text-[10px] text-zinc-600 mt-1.5 leading-relaxed">
              {s.reasoning.slice(0, 100)}{s.reasoning.length > 100 ? "..." : ""}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
