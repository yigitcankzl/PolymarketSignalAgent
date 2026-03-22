"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Loader2, Check, Zap } from "lucide-react";

interface PipelineStep {
  step: number;
  total_steps: number;
  label: string;
  detail: string;
  progress: number;
  running: boolean;
}

const STEP_ICONS: Record<number, string> = {
  1: "Fetching markets",
  2: "Gathering news",
  3: "LLM analysis",
  4: "Signal generation",
  5: "Arbitrage scan",
  6: "Exporting",
  7: "Complete",
};

export function PipelineStatus({ isRunning }: { isRunning: boolean }) {
  const [status, setStatus] = useState<PipelineStep | null>(null);

  useEffect(() => {
    if (!isRunning) {
      setStatus(null);
      return;
    }

    const poll = setInterval(async () => {
      try {
        const resp = await fetch("/api/pipeline-status");
        const data = await resp.json();
        setStatus(data);
        if (!data.running && data.step >= data.total_steps) {
          setTimeout(() => setStatus(null), 5000);
        }
      } catch {
        // ignore
      }
    }, 1500);

    return () => clearInterval(poll);
  }, [isRunning]);

  if (!status || (!isRunning && !status.running && status.step === 0)) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: "auto" }}
        exit={{ opacity: 0, height: 0 }}
        className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 overflow-hidden"
      >
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-semibold text-white">Pipeline Execution</h2>
          {status.running && (
            <Loader2 className="w-3.5 h-3.5 text-blue-400 animate-spin ml-auto" />
          )}
        </div>

        {/* Progress bar */}
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden mb-4">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${status.progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Steps */}
        <div className="space-y-2">
          {Array.from({ length: status.total_steps }, (_, i) => i + 1).map((stepNum) => {
            const isComplete = stepNum < status.step || (stepNum === status.step && !status.running);
            const isCurrent = stepNum === status.step && status.running;

            return (
              <div key={stepNum} className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] ${
                  isComplete ? "bg-green-500/20 text-green-400" :
                  isCurrent ? "bg-blue-500/20 text-blue-400" :
                  "bg-zinc-800 text-zinc-600"
                }`}>
                  {isComplete ? <Check className="w-3 h-3" /> :
                   isCurrent ? <Loader2 className="w-3 h-3 animate-spin" /> :
                   stepNum}
                </div>
                <div className="flex-1">
                  <span className={`text-xs ${
                    isComplete ? "text-zinc-400" :
                    isCurrent ? "text-white font-medium" :
                    "text-zinc-600"
                  }`}>
                    {STEP_ICONS[stepNum] || `Step ${stepNum}`}
                  </span>
                  {isCurrent && status.detail && (
                    <p className="text-[10px] text-zinc-500 mt-0.5">{status.detail}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Completion message */}
        {!status.running && status.step >= status.total_steps && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-3 pt-3 border-t border-zinc-800 text-xs text-green-400"
          >
            {status.detail}
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
