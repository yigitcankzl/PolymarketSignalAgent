"use client";

import { motion } from "motion/react";
import { ArrowRightLeft, ExternalLink, TrendingUp } from "lucide-react";
import { formatPercent } from "@/lib/utils";

interface CrossPlatformArb {
  type: string;
  polymarket: {
    id: string;
    question: string;
    yes_price: number;
    slug: string;
  };
  kalshi: {
    id: string;
    question: string;
    yes_price: number;
  };
  price_difference: number;
  profit_potential_pct: number;
  action: string;
  buy_platform: string;
  sell_platform: string;
  buy_price: number;
  sell_price: number;
  synthesis_url: string;
}

interface ArbitragePanelProps {
  crossPlatform: CrossPlatformArb[];
  totalOpportunities: number;
}

export function ArbitragePanel({ crossPlatform, totalOpportunities }: ArbitragePanelProps) {
  if (!crossPlatform.length) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.9, duration: 0.5 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="w-4 h-4 text-amber-400" />
          <div>
            <h2 className="text-sm font-semibold text-white">Cross-Platform Arbitrage</h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Polymarket vs Kalshi price gaps &middot; Trade via{" "}
              <a
                href="https://synthesis.trade"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300"
              >
                Synthesis.trade
              </a>
            </p>
          </div>
        </div>
        <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-1 rounded-full">
          {totalOpportunities} found
        </span>
      </div>

      <div className="divide-y divide-zinc-800/50">
        {crossPlatform.map((arb, i) => (
          <div key={i} className="px-5 py-3 hover:bg-zinc-800/20 transition-colors">
            <p className="text-xs text-zinc-300 mb-2 leading-relaxed">
              {arb.polymarket.question}
            </p>

            {/* Price comparison */}
            <div className="flex items-center gap-2 mb-2">
              <div className="flex-1 flex items-center justify-between bg-zinc-800/50 rounded-lg px-3 py-1.5">
                <span className="text-[10px] text-zinc-500 uppercase">Polymarket</span>
                <span className="text-xs font-mono text-zinc-200">
                  {formatPercent(arb.polymarket.yes_price)}
                </span>
              </div>
              <ArrowRightLeft className="w-3.5 h-3.5 text-zinc-600 shrink-0" />
              <div className="flex-1 flex items-center justify-between bg-zinc-800/50 rounded-lg px-3 py-1.5">
                <span className="text-[10px] text-zinc-500 uppercase">Kalshi</span>
                <span className="text-xs font-mono text-zinc-200">
                  {formatPercent(arb.kalshi.yes_price)}
                </span>
              </div>
            </div>

            {/* Profit and action */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3 text-green-400" />
                  <span className="text-xs font-mono text-green-400 font-medium">
                    +{arb.profit_potential_pct.toFixed(1)}%
                  </span>
                </div>
                <span className="text-[10px] text-zinc-500">
                  {arb.action}
                </span>
              </div>

              {arb.synthesis_url && (
                <a
                  href={arb.synthesis_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[10px] text-blue-400 hover:text-blue-300 transition-colors bg-blue-500/10 px-2 py-1 rounded-full"
                >
                  <ExternalLink className="w-2.5 h-2.5" />
                  Trade on Synthesis
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
