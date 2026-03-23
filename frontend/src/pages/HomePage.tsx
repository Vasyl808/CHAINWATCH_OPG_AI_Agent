import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldAlert, Home } from "lucide-react";

import { useAnalysisStore } from "@/store/analysisStore";
import { useAnalysis } from "@/api/useAnalysis";

import { AddressInput } from "@/components/analysis/AddressInput";
import { StepProgress } from "@/components/analysis/StepProgress";
import { ToolCallFeed } from "@/components/analysis/ToolCallFeed";
import { ScanningVisual } from "@/components/analysis/ScanningVisual";
import { ReportDisplay } from "@/components/analysis/ReportDisplay";
import { TerminalLog } from "@/components/ui/TerminalLog";
import { CyberPanel } from "@/components/ui/CyberPanel";
import { SupportedNetworks } from "@/components/analysis/SupportedNetworks";
import { TokenSelectionDialog } from "@/components/analysis/TokenSelectionDialog";

export function HomePage() {
  const {
    phase,
    address,
    steps,
    toolCalls,
    statusMessages,
    report,
    error,
  } = useAnalysisStore();

  const { startAnalysis, cancel } = useAnalysis();
  const reset = useAnalysisStore((s) => s.reset);
  const isIdle = phase === "idle";
  const isSelecting = phase === "selecting";
  const isComplete = phase === "complete";
  const isError = phase === "error";
  const isRunning = !isIdle && !isSelecting && !isComplete && !isError;

  useEffect(() => {
    if (!isIdle) {
      window.scrollTo({ top: 0, left: 0, behavior: "auto" });
    }
  }, [isIdle, phase]);

  const handleSelectAnother = () => {
    useAnalysisStore.getState().resetForNewToken();
  };

  return (
    <main className="min-h-screen pt-20 pb-16 px-4">
      <div className="max-w-7xl mx-auto">
        <AnimatePresence mode="wait">
          {/* IDLE: show input */}
          {isIdle && (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, y: -20 }}
              className="flex flex-col items-center justify-center min-h-[80vh]"
            >
              <AddressInput onSubmit={startAnalysis} />

              {/* Features row */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-4xl"
              >
                {[
                  { icon: "[Omnichain]", label: "50+ Networks", desc: "Native auto-discovery across EVM, Solana, Sui, TON, TRON, Cosmos, and Bitcoin." },
                  { icon: "[Yield & Risk]", label: "Deep Analysis", desc: "Live yield farming opportunities, hack history audits, and news sentiment scoring." },
                  { icon: "[TEE Agent]", label: "TEE Secured Agent", desc: "Verifiable AI inference using a strict 6-step analytical reasoning algorithm." },
                ].map((f) => (
                  <div
                    key={f.label}
                    className="glass-panel p-6 text-center space-y-3 hover:-translate-y-1 transition-transform duration-300"
                  >
                    <div className="text-xl mb-2 font-mono text-brand-600 font-bold">{f.icon}</div>
                    <h3 className="font-sans text-sm font-bold text-gray-900 uppercase tracking-widest">
                      {f.label}
                    </h3>
                    <p className="font-sans text-xs text-gray-500 leading-relaxed font-medium">
                      {f.desc}
                    </p>
                  </div>
                ))}
              </motion.div>

              {/* Supported Networks Info */}
              <SupportedNetworks />
            </motion.div>
          )}

          {/* SELECTING: choose a token */}
          {isSelecting && <TokenSelectionDialog key="selecting" />}

          {/* RUNNING: live analysis dashboard */}
          {isRunning && (
            <motion.div
              key="running"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-8"
            >
              {/* Top bar */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4">
                <div>
                  <button
                    onClick={() => reset()}
                    className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-brand-600 transition-colors mb-2"
                  >
                    <Home className="w-4 h-4" /> Back to Home
                  </button>
                  <h1 className="font-sans text-2xl font-extrabold text-gray-900 tracking-tight">Active Analysis</h1>
                  <p className="font-mono text-sm text-brand-600 mt-1 bg-brand-50 px-3 py-1 rounded inline-block">
                    {address}
                  </p>
                </div>
                <button
                  onClick={cancel}
                  className="btn-ghost"
                >
                  <ShieldAlert className="w-4 h-4 mr-2" />
                  Abort Scan
                </button>
              </div>

              {/* Dashboard grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* LEFT: radar + steps */}
                <div className="space-y-6">
                  <CyberPanel label="Telemetry Sync" accent="cyan" className="p-2">
                    <ScanningVisual
                      address={address}
                      phase={phase}
                    />
                  </CyberPanel>

                  <CyberPanel label="Analysis Pipeline" accent="purple" className="p-4">
                    <StepProgress steps={steps} />
                  </CyberPanel>
                </div>

                {/* CENTER+RIGHT: tool feed + terminal */}
                <div className="lg:col-span-2 space-y-6">
                  <CyberPanel label="Agent Reasoning Stream" accent="gold" className="p-4 bg-gray-50/50">
                    <ToolCallFeed toolCalls={toolCalls} />
                  </CyberPanel>

                  <CyberPanel label="System Execution Log" accent="pink" className="p-0 bg-white">
                    <TerminalLog messages={statusMessages} />
                  </CyberPanel>
                </div>
              </div>
            </motion.div>
          )}

          {/* COMPLETE: report */}
          {isComplete && report && (
            <motion.div
              key="complete"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6"
            >
              {/* Sidebar: steps summary */}
              <div className="space-y-6">
                <button
                  onClick={() => reset()}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-brand-600 transition-colors mb-2"
                >
                  <Home className="w-4 h-4" /> Back to Home
                </button>
                <CyberPanel label="Verification Pipeline" accent="cyan" className="p-4">
                  <StepProgress steps={steps} />
                </CyberPanel>

                <CyberPanel label="Tools Executed" accent="gold" className="p-5">
                  <div className="space-y-3">
                    {toolCalls.map((tc, i) => (
                      <div key={i} className="flex justify-between items-center bg-slate-50 border border-slate-100 rounded-lg px-3 py-2">
                        <span className="font-sans text-xs font-semibold text-slate-700 capitalize">{tc.name.replace("get_", "").replace("_", " ")}</span>
                        <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center">
                          <span className="text-emerald-600 text-[10px] font-bold">OK</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-5 pt-4 border-t border-gray-100">
                    <p className="font-sans text-xs font-bold text-gray-500 uppercase tracking-widest text-center">
                      Successful {toolCalls.length} Agent Invocations
                    </p>
                  </div>
                </CyberPanel>
              </div>

              {/* Main report */}
              <div className="lg:col-span-2 space-y-6">
                <ReportDisplay
                  report={report}
                  address={address}
                  onReset={cancel}
                />
                
                <div className="flex justify-center mt-8">
                  <button 
                    onClick={handleSelectAnother}
                    className="btn-primary shadow-lg border border-brand-200"
                  >
                    Analyze Another Asset
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {/* ERROR */}
          {isError && (
            <motion.div
              key="error"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-col items-center justify-center min-h-[60vh] gap-4"
            >
              <div className="glass-panel p-10 max-w-lg w-full text-center space-y-6 border-rose-100 bg-rose-50/30">
                <div className="w-16 h-16 rounded-full bg-rose-100 mx-auto flex items-center justify-center shadow-sm">
                  <ShieldAlert className="w-8 h-8 text-rose-500" />
                </div>
                <div>
                  <h2 className="font-sans text-lg font-bold text-gray-900 tracking-tight mb-2">
                    Analysis Failed
                  </h2>
                  <p className="font-sans text-sm text-gray-600 break-words leading-relaxed">
                    {error}
                  </p>
                </div>
                <button
                  onClick={cancel}
                  className="btn-primary w-full shadow-md"
                >
                  Return to Dashboard
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
