"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Wallet, ArrowUpDown, DollarSign, TrendingUp } from "lucide-react";

interface TradingData {
  status: string;
  wallet_id?: string;
  balance?: Record<string, unknown>;
  positions?: Array<Record<string, unknown>>;
  pnl?: Record<string, unknown>;
  orders?: Array<Record<string, unknown>>;
  deposit_address?: string;
}

export function TradingPanel() {
  const [data, setData] = useState<TradingData | null>(null);

  useEffect(() => {
    fetch("/api/trading")
      .then((r) => r.json())
      .then(setData)
      .catch(() => {});
  }, []);

  if (!data || data.status === "not_configured") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45, duration: 0.5 }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5"
      >
        <div className="flex items-center gap-2 mb-3">
          <Wallet className="w-4 h-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-white">Live Trading</h2>
        </div>
        <p className="text-xs text-zinc-500">
          Run pipeline with <code className="text-blue-400">--trade</code> flag to enable
          automated order execution via Synthesis.trade
        </p>
        <div className="mt-3 text-[10px] text-zinc-600 space-y-1">
          <p>python3 -m engine.main --markets 10 --trade</p>
        </div>
      </motion.div>
    );
  }

  const balance = data.balance || {};
  const positions = data.positions || [];
  const orders = data.orders || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.45, duration: 0.5 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden"
    >
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet className="w-4 h-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-white">Live Trading</h2>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 border border-green-500/30">
          {data.status}
        </span>
      </div>

      <div className="divide-y divide-zinc-800/50">
        <div className="flex items-center justify-between px-5 py-2.5">
          <div className="flex items-center gap-2">
            <DollarSign className="w-3.5 h-3.5 text-zinc-500" />
            <span className="text-xs text-zinc-500">Balance</span>
          </div>
          <span className="text-sm font-mono text-white">
            {JSON.stringify(balance).includes("0") ? "$0.00" : JSON.stringify(balance).slice(0, 20)}
          </span>
        </div>

        <div className="flex items-center justify-between px-5 py-2.5">
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-3.5 h-3.5 text-zinc-500" />
            <span className="text-xs text-zinc-500">Positions</span>
          </div>
          <span className="text-sm font-mono text-zinc-300">{positions.length}</span>
        </div>

        <div className="flex items-center justify-between px-5 py-2.5">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-zinc-500" />
            <span className="text-xs text-zinc-500">Orders</span>
          </div>
          <span className="text-sm font-mono text-zinc-300">{orders.length}</span>
        </div>

        {data.wallet_id && (
          <div className="px-5 py-2.5">
            <span className="text-[10px] text-zinc-600">Wallet: {data.wallet_id.slice(0, 16)}...</span>
          </div>
        )}

        {data.deposit_address && (
          <div className="px-5 py-2.5">
            <span className="text-[10px] text-zinc-600">Deposit: {data.deposit_address.slice(0, 20)}...</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
