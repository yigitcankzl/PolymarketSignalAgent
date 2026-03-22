"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Toaster, toast } from "sonner";
import { Header } from "@/components/header";
import { StatsOverview } from "@/components/stats-overview";
import { SignalTable } from "@/components/signal-table";
import { PnLChart } from "@/components/pnl-chart";
import { EdgeChart } from "@/components/edge-chart";
import { BacktestPanel } from "@/components/backtest-panel";
import { SignalBreakdown } from "@/components/signal-breakdown";
import { TopSignals } from "@/components/top-signals";
import { ArbitragePanel } from "@/components/arbitrage-panel";
import { TradingPanel } from "@/components/trading-panel";
import { DashboardSkeleton } from "@/components/skeleton";

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
  kelly_fraction?: number;
  polymarket_url?: string;
  raw_probability?: number;
  ensemble?: {
    models_used: number;
    model_predictions: Record<string, number>;
    spread: number;
    calibrated: number;
  };
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

const REFRESH_INTERVAL = 30;

interface ArbitrageData {
  cross_platform: Array<{
    type: string;
    polymarket: { id: string; question: string; yes_price: number; slug: string };
    kalshi: { id: string; question: string; yes_price: number };
    price_difference: number;
    profit_potential_pct: number;
    action: string;
    buy_platform: string;
    sell_platform: string;
    buy_price: number;
    sell_price: number;
    synthesis_url: string;
  }>;
  total_opportunities: number;
}

export default function Dashboard() {
  const [signals, setSignals] = useState<SignalData | null>(null);
  const [backtest, setBacktest] = useState<BacktestData | null>(null);
  const [markets, setMarkets] = useState<MarketsData | null>(null);
  const [arbitrage, setArbitrage] = useState<ArbitrageData | null>(null);
  const [loading, setLoading] = useState(true);
  const prevSignalCount = useRef<number>(0);

  const fetchData = useCallback(async () => {
    try {
      const [sigRes, btRes, mkRes, arbRes] = await Promise.all([
        fetch("/api/signals"),
        fetch("/api/backtest"),
        fetch("/api/markets"),
        fetch("/api/arbitrage"),
      ]);
      const [sigData, btData, mkData, arbData] = await Promise.all([
        sigRes.json(),
        btRes.json(),
        mkRes.json(),
        arbRes.json(),
      ]);

      // Detect new signals
      if (prevSignalCount.current > 0 && sigData.total_signals > prevSignalCount.current) {
        const diff = sigData.total_signals - prevSignalCount.current;
        toast.success(`${diff} new signal${diff > 1 ? "s" : ""} detected`, {
          description: "Dashboard updated with latest data",
        });
      }
      prevSignalCount.current = sigData.total_signals;

      setSignals(sigData);
      setBacktest(btData);
      setMarkets(mkData);
      setArbitrage(arbData);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <DashboardSkeleton />;
  }

  const allSignals = signals?.signals || [];

  return (
    <div className="min-h-screen bg-zinc-950">
      <Toaster
        theme="dark"
        position="top-right"
        toastOptions={{
          style: { background: "#18181b", border: "1px solid #3f3f46", color: "#fafafa" },
        }}
      />

      <Header
        marketCount={markets?.count || 0}
        lastRun={signals?.generated_at ? new Date(signals.generated_at).toLocaleString() : ""}
        onRefresh={fetchData}
        refreshInterval={REFRESH_INTERVAL}
      />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        <StatsOverview
          metrics={backtest?.metrics || null}
          signalCount={signals?.total_signals || 0}
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <SignalTable signals={allSignals} />
            <PnLChart data={backtest?.pnl_curve || []} />
            <EdgeChart signals={allSignals} />
          </div>

          <div className="space-y-6">
            <TradingPanel />
            <BacktestPanel metrics={backtest?.metrics || null} />
            <ArbitragePanel
              crossPlatform={arbitrage?.cross_platform || []}
              totalOpportunities={arbitrage?.total_opportunities || 0}
            />
            <SignalBreakdown signals={allSignals} />
            <TopSignals signals={allSignals} />
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-800 mt-12 py-6 text-center text-xs text-zinc-600">
        <span>Polymarket Signal Agent — Built for ETHGlobal Hackathon 2026</span>
        <span className="mx-2">&middot;</span>
        <a
          href="https://synthesis.trade"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 transition-colors"
        >
          Powered by Synthesis.trade
        </a>
      </footer>
    </div>
  );
}
