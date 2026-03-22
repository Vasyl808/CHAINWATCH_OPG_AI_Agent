import { motion, AnimatePresence } from "framer-motion";
import { Activity, ChevronDown, ChevronRight, Check } from "lucide-react";
import { useState } from "react";
import type { ToolCallEntry } from "@/types";
import { formatToolName, cn } from "@/utils";

interface Props {
  toolCalls: ToolCallEntry[];
}

const TOOL_COLORS: Record<string, string> = {
  get_omnichain_balance: "text-brand-600 bg-brand-50 border-brand-100",
  get_defi_yields: "text-amber-600 bg-amber-50 border-amber-100",
  search_crypto_news: "text-violet-600 bg-violet-50 border-violet-100",
};

function ToolCallItem({ entry }: { entry: ToolCallEntry }) {
  const [expanded, setExpanded] = useState(false);
  const colorClass = TOOL_COLORS[entry.name] ?? "text-slate-600 bg-slate-50 border-slate-100";
  const hasResult = Boolean(entry.result);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("bg-white border rounded-xl overflow-hidden shadow-sm", colorClass.split(" ")[2])}
    >
      <button
        className={cn(
          "w-full flex items-center gap-3 px-4 py-3 text-left",
          "hover:bg-slate-50 transition-colors"
        )}
        onClick={() => setExpanded((p) => !p)}
      >
        <div className={cn("w-6 h-6 rounded-md flex items-center justify-center shrink-0", colorClass.split(" ")[1])}>
          <Activity className={cn("w-3.5 h-3.5", colorClass.split(" ")[0])} />
        </div>
        
        <span className="font-sans text-sm font-semibold text-gray-800 flex-1">
          {formatToolName(entry.name)}
        </span>
        {hasResult ? (
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-100">
            <Check className="w-3 h-3 text-emerald-600" />
            <span className="font-sans text-[10px] font-bold tracking-wider text-emerald-600 uppercase">Done</span>
          </div>
        ) : (
          <span className="font-sans text-[10px] font-bold tracking-wider text-brand-500 uppercase animate-pulse">Running</span>
        )}
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400 ml-1" />
        ) : (
          <ChevronRight className="w-4 h-4 text-gray-400 ml-1" />
        )}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-gray-100 overflow-hidden bg-slate-50/50"
          >
            <div className="px-4 py-3 space-y-3">
              {/* Args */}
              <div>
                <p className="font-sans text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-1.5">
                  Input Arguments
                </p>
                <pre className="font-mono text-[11px] text-gray-700 whitespace-pre-wrap break-all bg-white rounded-lg p-3 border border-gray-200 shadow-sm">
                  {JSON.stringify(entry.args, null, 2)}
                </pre>
              </div>

              {/* Result */}
              {entry.result && (
                <div>
                  <p className="font-sans text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-1.5">
                    Agent Output
                  </p>
                  <pre className="font-mono text-[11px] text-gray-700 whitespace-pre-wrap break-all bg-white rounded-lg p-3 border border-gray-200 shadow-sm max-h-48 overflow-y-auto">
                    {entry.result}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function ToolCallFeed({ toolCalls }: Props) {
  if (toolCalls.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-gray-400">
        <Activity className="w-8 h-8 mb-3 opacity-50" />
        <p className="font-sans text-sm font-medium">Waiting for agent activity...</p>
      </div>
    );
  }

  return (
    <div className="space-y-3 overflow-y-auto pr-1 pb-1" style={{ maxHeight: "400px" }}>
      <AnimatePresence initial={false}>
        {toolCalls.map((tc) => (
          <ToolCallItem key={tc.id} entry={tc} />
        ))}
      </AnimatePresence>
    </div>
  );
}
