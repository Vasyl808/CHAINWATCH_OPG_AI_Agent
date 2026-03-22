import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Coins, ChevronRight, ArrowLeft, Network, Home } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";
import { useAnalysis } from "@/api/useAnalysis";
import { CyberPanel } from "@/components/ui/CyberPanel";

export function TokenSelectionDialog() {
  const { portfolio, address } = useAnalysisStore();
  const { startTokenAnalysis } = useAnalysis();
  const reset = useAnalysisStore((s) => s.reset);
  
  const [selectedNetwork, setSelectedNetwork] = useState<string | null>(null);

  const handleSelectToken = (tokenSymbol: string, network: string) => {
    startTokenAnalysis(tokenSymbol, network);
  };

  const networkStats = useMemo(() => {
    const stats: Record<string, { tokenCount: number; totalUsd: number }> = {};
    for (const t of portfolio) {
      if (!stats[t.network]) stats[t.network] = { tokenCount: 0, totalUsd: 0 };
      stats[t.network].tokenCount += 1;
      stats[t.network].totalUsd += (t.usd_value || 0);
    }
    return stats;
  }, [portfolio]);

  const networks = Object.keys(networkStats).sort((a, b) => networkStats[b].totalUsd - networkStats[a].totalUsd);

  return (
    <motion.div
      key="selecting-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="max-w-4xl mx-auto mt-8"
    >
      <AnimatePresence mode="wait">
        {!selectedNetwork ? (
          <motion.div key="step-1" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
            <div className="mb-8 text-center sm:text-left">
              <button
                onClick={() => reset()}
                className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-brand-600 transition-colors mb-4 mx-auto sm:mx-0"
              >
                <Home className="w-4 h-4" /> Back to Home
              </button>
              <h1 className="font-sans text-3xl font-extrabold text-gray-900 tracking-tight">
                Select Network
              </h1>
              <p className="font-sans text-sm text-gray-500 mt-2 max-w-2xl">
                We found assets across {networks.length} networks on <span className="font-mono text-brand-600 bg-brand-50 px-2 py-0.5 rounded">{address}</span>.
                Choose a network to view its assets.
              </p>
            </div>

            <CyberPanel label="Available Networks" accent="cyan" className="p-0 overflow-hidden bg-white">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0">
                {networks.map((net) => (
                  <motion.div
                    key={net}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelectedNetwork(net)}
                    className="p-5 border-b sm:border-b-0 sm:border-r border-gray-100 hover:bg-slate-50 cursor-pointer transition-colors group flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 group-hover:text-brand-500 group-hover:bg-brand-50 transition-colors">
                          <Network className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-900 text-lg leading-tight uppercase tracking-wide">{net}</h3>
                          <span className="text-[10px] font-bold tracking-wider text-gray-400">{networkStats[net].tokenCount} assets</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-brand-500 transition-colors" />
                    </div>
                    {networkStats[net].totalUsd > 0 && (
                      <div className="mt-2 text-sm">
                        <span className="text-gray-500 uppercase text-[10px] tracking-wider block">Total Network Value</span>
                        <span className="font-mono font-bold text-emerald-600">${networkStats[net].totalUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
              {networks.length === 0 && (
                <div className="p-12 text-center">
                  <Coins className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="font-bold text-gray-900">No assets found</h3>
                  <p className="text-sm text-gray-500 mt-1">This wallet appears to be empty or APIs are currently unreachable.</p>
                </div>
              )}
            </CyberPanel>
          </motion.div>
        ) : (
          <motion.div key="step-2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
            <div className="mb-8">
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={() => reset()}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-brand-600 transition-colors"
                >
                  <Home className="w-4 h-4" /> Back to Home
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={() => setSelectedNetwork(null)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-brand-600 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" /> Back to Networks
                </button>
              </div>
              <h1 className="font-sans text-3xl font-extrabold text-gray-900 tracking-tight">
                Select Asset on <span className="uppercase text-brand-600">{selectedNetwork}</span>
              </h1>
            </div>

            <CyberPanel label={`${selectedNetwork} Assets`} accent="cyan" className="p-0 overflow-hidden bg-white">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0">
                {portfolio.filter(t => t.network === selectedNetwork).sort((a: any, b: any) => (b.usd_value || 0) - (a.usd_value || 0)).map((token, idx) => (
                  <motion.div
                    key={`${token.network}-${token.symbol}-${idx}`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleSelectToken(token.symbol, token.network)}
                    className="p-5 border-b sm:border-b-0 sm:border-r border-gray-100 hover:bg-slate-50 cursor-pointer transition-colors group flex flex-col justify-between"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 group-hover:text-brand-500 group-hover:bg-brand-50 transition-colors">
                          <Coins className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="font-bold text-gray-900 text-lg leading-tight">{token.symbol}</h3>
                          <span className="text-[10px] font-bold tracking-wider text-gray-400 uppercase">{token.network}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-brand-500 transition-colors" />
                    </div>

                    <div className="space-y-1 mt-2">
                      <div className="flex justify-between items-baseline">
                        <span className="text-xs text-gray-500">Balance</span>
                        <span className="font-mono font-medium text-gray-900">{token.amount.toLocaleString(undefined, { maximumFractionDigits: 3 })}</span>
                      </div>
                      <div className="flex justify-between items-baseline">
                        <span className="text-xs text-gray-500">Value (USD)</span>
                        <span className="font-mono font-bold text-emerald-600">
                          {token.usd_value && token.usd_value > 0 ? `$${token.usd_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "-"}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-100/50">
                      <div className="text-xs font-semibold text-brand-600 group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
                        Analyze this asset <ChevronRight className="w-3 h-3" />
                      </div>
                    </div>
                  </motion.div>
                ))}
            </div>
            </CyberPanel>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
