import { useState, type FormEvent } from "react";
import { motion } from "framer-motion";
import { Search, Zap, Shield } from "lucide-react";
import { CyberPanel } from "@/components/ui/CyberPanel";
import { detectChain, cn } from "@/utils";

interface Props {
  onSubmit: (address: string) => void;
  disabled?: boolean;
}

const CHAIN_COLORS: Record<string, string> = {
  EVM: "text-brand-700 border-brand-200 bg-brand-50",
  SOL: "text-purple-700 border-purple-200 bg-purple-50",
  SUI: "text-blue-700 border-blue-200 bg-blue-50",
  BTC: "text-amber-700 border-amber-200 bg-amber-50",
  UNKNOWN: "text-gray-500 border-gray-200 bg-gray-50",
};


export function AddressInput({ onSubmit, disabled = false }: Props) {
  const [value, setValue] = useState("");
  const chain = value.trim() ? detectChain(value.trim()) : null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim()) onSubmit(value.trim());
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Hero */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="text-center mb-12"
      >
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-full bg-brand-50 flex items-center justify-center border border-brand-100">
            <Shield className="w-4 h-4 text-brand-600" />
          </div>
          <span className="font-sans text-xs font-semibold tracking-[0.2em] text-gray-500 rounded-full bg-white px-4 py-1.5 shadow-sm border border-gray-100 uppercase">
            OpenGradient TEE
          </span>
          <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center border border-amber-100">
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
        </div>

        <h1 className="font-sans text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900 mb-6 drop-shadow-sm">
          CHAINWATCH
        </h1>
        <p className="font-sans text-base sm:text-lg text-gray-500 max-w-lg mx-auto leading-relaxed">
          Advanced blockchain security intelligence and AI-powered wallet analysis.
        </p>
      </motion.div>

      {/* Input panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="glass-panel p-2 sm:p-3"
      >
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-grow">
            <input
              className="clean-input !py-4 pr-16 shadow-none"
              placeholder="0x... or Solana base58 or SUI / BTC address"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              disabled={disabled}
              spellCheck={false}
              autoComplete="off"
            />
            {chain && (
              <span
                className={cn(
                  "absolute right-4 top-1/2 -translate-y-1/2",
                  "font-sans text-[10px] font-bold tracking-wider uppercase",
                  "px-2.5 py-1 rounded-md border",
                  CHAIN_COLORS[chain]
                )}
              >
                {chain}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="btn-primary sm:w-auto w-full flex items-center justify-center gap-2 !px-8"
          >
            <Search className="w-4 h-4" />
            <span>ANALYZE</span>
          </button>
        </form>

      </motion.div>
    </div>
  );
}
