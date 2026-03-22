"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { StatsOverview } from "@/components/stats-overview";
import { SignalTable } from "@/components/signal-table";
import { PnLChart } from "@/components/pnl-chart";
import { EdgeChart } from "@/components/edge-chart";
import { BacktestPanel } from "@/components/backtest-panel";
import { SignalBreakdown } from "@/components/signal-breakdown";
import { TopSignals } from "@/components/top-signals";

interface SignalEntry {
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
  timestamp: string;
  news_count: number;
}

interface PnLPoint {
  trade_number: number;
  question: string;
  signal: string;
  pnl: number;
  cumulative_pnl: number;
}

interface Trade {
  market_id: string;
  question: string;
  signal: string;
  pnl: number;
  correct: boolean;
}

interface Metrics {
  total_signals: number;
  hit_rate: number;
  avg_edge: number;
  sharpe_ratio: number;
  total_pnl: number;
  avg_pnl: number;
  max_drawdown: number;
  profit_factor: number;
  win_count: number;
  loss_count: number;
  best_trade: number;
  worst_trade: number;
  correct_signals: number;
  win_rate_by_signal: Record<string, number>;
}

interface SignalData {
  generated_at: string;
  total_signals: number;
  actionable_signals: number;
  signals: SignalEntry[];
}

interface BacktestData {
  metrics: Metrics | null;
  pnl_curve: PnLPoint[];
  trades: Trade[];
}

interface MarketsData {
  timestamp: string;
  count: number;
}

export default function Dashboard() {
  const [signals, setSignals] = useState<SignalData | null>(null);
  const [backtest, setBacktest] = useState<BacktestData | null>(null);
  const [markets, setMarkets] = useState<MarketsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [sigRes, btRes, mkRes] = await Promise.all([
          fetch("/api/signals"),
          fetch("/api/backtest"),
          fetch("/api/markets"),
        ]);
        const [sigData, btData, mkData] = await Promise.all([
          sigRes.json(),
          btRes.json(),
          mkRes.json(),
        ]);
        setSignals(sigData);
        setBacktest(btData);
        setMarkets(mkData);
      } catch (err) {
        console.error("Failed to fetch data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-zinc-500 text-sm">Loading dashboard...</div>
      </div>
    );
  }

  const allSignals = signals?.signals || [];

  return (
    <div className="min-h-screen bg-zinc-950">
      <Header
        marketCount={markets?.count || 0}
        lastRun={signals?.generated_at ? new Date(signals.generated_at).toLocaleString() : ""}
      />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Stats Overview */}
        <StatsOverview
          metrics={backtest?.metrics || null}
          signalCount={signals?.total_signals || 0}
        />

        {/* Main Grid: 2 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - wide */}
          <div className="lg:col-span-2 space-y-6">
            <SignalTable signals={allSignals} />
            <PnLChart data={backtest?.pnl_curve || []} />
            <EdgeChart signals={allSignals} />
          </div>

          {/* Right column - narrow */}
          <div className="space-y-6">
            <BacktestPanel metrics={backtest?.metrics || null} />
            <SignalBreakdown signals={allSignals} />
            <TopSignals signals={allSignals} />
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-800 mt-12 py-6 text-center text-xs text-zinc-600">
        Polymarket Signal Agent — Built for ETHGlobal Hackathon 2026
      </footer>
    </div>
  );
}
