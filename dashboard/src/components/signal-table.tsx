"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { ChevronDown, ExternalLink, ShoppingCart } from "lucide-react";
import { toast } from "sonner";
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
  key_factors: string[];
  news_count: number;
  kelly_fraction?: number;
  sparkline?: number[];
  polymarket_url?: string;
  ensemble?: {
    models_used: number;
    model_predictions: Record<string, number>;
    spread: number;
  };
}

interface SignalTableProps {
  signals: Signal[];
}

function SignalDetail({ signal }: { signal: Signal }) {
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: "auto", opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.3 }}
      className="overflow-hidden"
    >
      <div className="px-5 py-4 bg-zinc-800/30 border-t border-zinc-700/50">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs font-semibold text-zinc-400 uppercase mb-2">AI Reasoning</h4>
            <p className="text-sm text-zinc-300 leading-relaxed">{signal.reasoning}</p>

            {signal.key_factors && signal.key_factors.length > 0 && (
              <div className="mt-3">
                <h4 className="text-xs font-semibold text-zinc-400 uppercase mb-1.5">Key Factors</h4>
                <div className="flex flex-wrap gap-1.5">
                  {signal.key_factors.map((factor, i) => (
                    <span key={i} className="text-[10px] px-2 py-0.5 bg-zinc-700/50 text-zinc-300 rounded-full">
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            {signal.kelly_fraction !== undefined && signal.kelly_fraction > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-zinc-400 uppercase mb-1">Position Size (Kelly)</h4>
                <div className="flex items-center gap-2">
                  <div className="h-2 bg-zinc-700 rounded-full flex-1">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${Math.min(signal.kelly_fraction * 100 / 5 * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-sm font-mono text-blue-400">{(signal.kelly_fraction * 100).toFixed(1)}%</span>
                </div>
              </div>
            )}

            {signal.ensemble && (
              <div>
                <h4 className="text-xs font-semibold text-zinc-400 uppercase mb-1.5">
                  Ensemble ({signal.ensemble.models_used} models)
                </h4>
                <div className="space-y-1">
                  {Object.entries(signal.ensemble.model_predictions).map(([model, prob]) => (
                    <div key={model} className="flex items-center justify-between text-xs">
                      <span className="text-zinc-500 truncate mr-2">{model.split("-").slice(0, 2).join("-")}</span>
                      <span className="text-zinc-300 font-mono">{formatPercent(prob)}</span>
                    </div>
                  ))}
                  <div className="flex items-center justify-between text-xs pt-1 border-t border-zinc-700/50">
                    <span className="text-zinc-400">Spread</span>
                    <span className={cn("font-mono", signal.ensemble.spread > 0.1 ? "text-amber-400" : "text-green-400")}>
                      {formatPercent(signal.ensemble.spread)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center gap-2 flex-wrap">
              {signal.signal.includes("BUY") && (
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const amount = signal.kelly_fraction ? Math.max(0.5, signal.kelly_fraction * 100).toFixed(2) : "1";
                    toast.info(`Placing BUY $${amount} order...`);
                    try {
                      const resp = await fetch("/api/trade", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ token_id: signal.market_id, side: "BUY", amount }),
                      });
                      const data = await resp.json();
                      if (data.success) toast.success(`Order placed: BUY $${amount}`);
                      else toast.error(data.error || data.order?.response || "Order failed");
                    } catch { toast.error("Order request failed"); }
                  }}
                  className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-full bg-green-600 hover:bg-green-500 text-white font-medium transition-colors"
                >
                  <ShoppingCart className="w-2.5 h-2.5" />
                  BUY ${signal.kelly_fraction ? Math.max(0.5, signal.kelly_fraction * 100).toFixed(0) : "1"}
                </button>
              )}
              {signal.signal.includes("SELL") && (
                <button
                  onClick={async (e) => {
                    e.stopPropagation();
                    const amount = signal.kelly_fraction ? Math.max(0.5, signal.kelly_fraction * 100).toFixed(2) : "1";
                    toast.info(`Placing SELL $${amount} order...`);
                    try {
                      const resp = await fetch("/api/trade", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ token_id: signal.market_id, side: "SELL", amount }),
                      });
                      const data = await resp.json();
                      if (data.success) toast.success(`Order placed: SELL $${amount}`);
                      else toast.error(data.error || data.order?.response || "Order failed");
                    } catch { toast.error("Order request failed"); }
                  }}
                  className="inline-flex items-center gap-1 text-[10px] px-2.5 py-1 rounded-full bg-red-600 hover:bg-red-500 text-white font-medium transition-colors"
                >
                  <ShoppingCart className="w-2.5 h-2.5" />
                  SELL ${signal.kelly_fraction ? Math.max(0.5, signal.kelly_fraction * 100).toFixed(0) : "1"}
                </button>
              )}
              {signal.polymarket_url && (
                <a
                  href={signal.polymarket_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
                >
                  <ExternalLink className="w-2.5 h-2.5" />
                  Polymarket
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function Sparkline({ data, width = 60, height = 20 }: { data: number[]; width?: number; height?: number }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data
    .map((v, i) => `${(i / (data.length - 1)) * width},${height - ((v - min) / range) * height}`)
    .join(" ");
  const isUp = data[data.length - 1] >= data[0];
  return (
    <svg width={width} height={height} className="inline-block">
      <polyline
        fill="none"
        stroke={isUp ? "#22c55e" : "#ef4444"}
        strokeWidth="1.5"
        points={points}
      />
    </svg>
  );
}

export function SignalTable({ signals }: SignalTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!signals.length) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center text-zinc-500">
        No signals available. Run the pipeline to generate signals.
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4, duration: 0.5 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-zinc-800">
        <h2 className="text-sm font-semibold text-white">Active Signals</h2>
        <p className="text-xs text-zinc-500 mt-1">Tap any signal to expand AI reasoning and ensemble details</p>
      </div>

      {/* Mobile card layout */}
      <div className="md:hidden divide-y divide-zinc-800/50">
        {signals.map((s) => (
          <div
            key={`mobile-${s.market_id}`}
            onClick={() => setExpandedId(expandedId === s.market_id ? null : s.market_id)}
            className="px-4 py-3 cursor-pointer hover:bg-zinc-800/20 transition-colors"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <p className="text-xs text-zinc-200 leading-relaxed flex-1">{s.question}</p>
              <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full border shrink-0", getSignalBg(s.signal))}>
                {s.signal}
              </span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-zinc-500">
              <span>Odds: {formatPercent(s.market_odds)}</span>
              <span>LLM: {formatPercent(s.llm_probability)}</span>
              <span className={s.edge > 0 ? "text-green-400" : "text-red-400"}>
                Edge: {s.edge > 0 ? "+" : ""}{formatPercent(s.edge)}
              </span>
              <span>Score: {s.score.toFixed(3)}</span>
            </div>
            <AnimatePresence>
              {expandedId === s.market_id && <SignalDetail signal={s} />}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Desktop table layout */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800 text-zinc-500 text-xs uppercase tracking-wider">
              <th className="w-8 px-2 py-3" />
              <th className="text-left px-3 py-3 font-medium">Market</th>
              <th className="text-center px-3 py-3 font-medium hidden md:table-cell">Trend</th>
              <th className="text-right px-3 py-3 font-medium">Odds</th>
              <th className="text-right px-3 py-3 font-medium">LLM</th>
              <th className="text-right px-3 py-3 font-medium">Edge</th>
              <th className="text-right px-3 py-3 font-medium">Conf</th>
              <th className="text-center px-3 py-3 font-medium">Signal</th>
              <th className="text-right px-3 py-3 font-medium">Kelly</th>
              <th className="text-right px-5 py-3 font-medium">Score</th>
            </tr>
          </thead>
          <tbody>
            {signals.map((s, i) => (
              <motion.tr
                key={s.market_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.03, duration: 0.3 }}
                className="contents"
              >
                <tr
                  onClick={() => setExpandedId(expandedId === s.market_id ? null : s.market_id)}
                  className={cn(
                    "border-b border-zinc-800/50 hover:bg-zinc-800/30 transition-colors cursor-pointer",
                    expandedId === s.market_id && "bg-zinc-800/20",
                  )}
                >
                  <td className="px-2 py-3">
                    <ChevronDown className={cn(
                      "w-3.5 h-3.5 text-zinc-600 transition-transform",
                      expandedId === s.market_id && "rotate-180"
                    )} />
                  </td>
                  <td className="px-3 py-3">
                    <p className="text-zinc-200 text-sm truncate max-w-xs">{s.question}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-zinc-600 text-[10px]">{s.news_count} news</span>
                      {s.ensemble && (
                        <span className="text-blue-400/60 text-[10px]">{s.ensemble.models_used} models</span>
                      )}
                    </div>
                  </td>
                  <td className="text-center px-3 py-3 hidden md:table-cell">
                    {s.sparkline && <Sparkline data={s.sparkline} />}
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
                      getSignalBg(s.signal),
                      (s.signal === "STRONG_BUY" || s.signal === "STRONG_SELL") && "animate-pulse"
                    )}>
                      {s.signal}
                    </span>
                  </td>
                  <td className="text-right px-3 py-3 text-blue-400/80 font-mono text-xs">
                    {s.kelly_fraction ? `${(s.kelly_fraction * 100).toFixed(1)}%` : "—"}
                  </td>
                  <td className="text-right px-5 py-3 text-zinc-200 font-mono text-xs font-medium">
                    {s.score.toFixed(4)}
                  </td>
                </tr>
                <AnimatePresence>
                  {expandedId === s.market_id && (
                    <tr>
                      <td colSpan={10}>
                        <SignalDetail signal={s} />
                      </td>
                    </tr>
                  )}
                </AnimatePresence>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}
