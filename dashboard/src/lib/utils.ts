import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatPnL(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(4)}`;
}

export function getSignalColor(signal: string): string {
  switch (signal) {
    case "STRONG_BUY":
      return "text-green-500";
    case "BUY":
      return "text-green-300";
    case "SELL":
      return "text-red-300";
    case "STRONG_SELL":
      return "text-red-500";
    default:
      return "text-gray-500";
  }
}

export function getSignalBg(signal: string): string {
  switch (signal) {
    case "STRONG_BUY":
      return "bg-green-500/20 text-green-400 border-green-500/30";
    case "BUY":
      return "bg-green-400/15 text-green-300 border-green-400/25";
    case "SELL":
      return "bg-red-400/15 text-red-300 border-red-400/25";
    case "STRONG_SELL":
      return "bg-red-500/20 text-red-400 border-red-500/30";
    default:
      return "bg-gray-500/15 text-gray-400 border-gray-500/25";
  }
}
