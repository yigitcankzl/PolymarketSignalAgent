"use client";

export function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-zinc-950 animate-pulse">
      {/* Header skeleton */}
      <div className="border-b border-zinc-800 bg-zinc-950/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-zinc-800" />
            <div>
              <div className="h-5 w-48 bg-zinc-800 rounded" />
              <div className="h-3 w-32 bg-zinc-800 rounded mt-1.5" />
            </div>
          </div>
          <div className="flex gap-4">
            <div className="h-4 w-24 bg-zinc-800 rounded" />
            <div className="h-4 w-16 bg-zinc-800 rounded" />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Stats skeleton */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-lg bg-zinc-800" />
                <div className="h-3 w-20 bg-zinc-800 rounded" />
              </div>
              <div className="h-7 w-16 bg-zinc-800 rounded" />
            </div>
          ))}
        </div>

        {/* Content skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Table skeleton */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800">
                <div className="h-4 w-32 bg-zinc-800 rounded" />
              </div>
              {[...Array(6)].map((_, i) => (
                <div key={i} className="px-5 py-3 border-b border-zinc-800/50 flex items-center gap-4">
                  <div className="h-4 w-64 bg-zinc-800 rounded flex-1" />
                  <div className="h-4 w-12 bg-zinc-800 rounded" />
                  <div className="h-4 w-12 bg-zinc-800 rounded" />
                  <div className="h-6 w-20 bg-zinc-800 rounded-full" />
                </div>
              ))}
            </div>
            {/* Chart skeleton */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
              <div className="h-4 w-28 bg-zinc-800 rounded mb-4" />
              <div className="h-64 bg-zinc-800/50 rounded-lg" />
            </div>
          </div>

          <div className="space-y-6">
            {/* Panel skeleton */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
              <div className="px-5 py-4 border-b border-zinc-800">
                <div className="h-4 w-28 bg-zinc-800 rounded" />
              </div>
              {[...Array(8)].map((_, i) => (
                <div key={i} className="px-5 py-2.5 flex items-center justify-between border-b border-zinc-800/30">
                  <div className="h-3 w-20 bg-zinc-800 rounded" />
                  <div className="h-3 w-12 bg-zinc-800 rounded" />
                </div>
              ))}
            </div>
            {/* Breakdown skeleton */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
              <div className="h-4 w-32 bg-zinc-800 rounded mb-4" />
              {[...Array(5)].map((_, i) => (
                <div key={i} className="mb-3">
                  <div className="flex justify-between mb-1">
                    <div className="h-5 w-20 bg-zinc-800 rounded-full" />
                    <div className="h-3 w-12 bg-zinc-800 rounded" />
                  </div>
                  <div className="h-1.5 bg-zinc-800 rounded-full" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
