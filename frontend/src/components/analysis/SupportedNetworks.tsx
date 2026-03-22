import { motion } from "framer-motion";
import { Info, Network } from "lucide-react";
import { cn } from "@/utils";

const networks = [
  {
    name: "Ethereum / EVM",
    logo: "/ethereum-eth-logo.svg",
    color: "text-blue-600",
    bg: "bg-slate-50",
    border: "border-blue-100",
    format: "0x + 40 hex digits",
    description: "Multichain support for 32+ EVM networks including Arbitrum, Base, and zkSync.",
    assets: "ETH, ERC-20 Tokens",
  },
  {
    name: "Solana",
    logo: "/solana-sol-logo.svg",
    color: "text-purple-600",
    bg: "bg-slate-50",
    border: "border-purple-100",
    format: "Base58 (32-44 characters)",
    description: "High-performance network with full SPL and Token-2022 support.",
    assets: "SOL, SPL Tokens",
  },
  {
    name: "Sui & Starknet",
    logo: "/sui-sui-logo.svg",
    color: "text-cyan-600",
    bg: "bg-slate-50",
    border: "border-cyan-100",
    format: "0x + 64 hex digits",
    description: "Object-centric Layer 1 and ZK-Rollup Layer 2 balance discovery.",
    assets: "SUI, STRK, Tokens",
  },
  {
    name: "Cosmos & TON",
    logo: null,
    color: "text-indigo-600",
    bg: "bg-slate-50",
    border: "border-indigo-100",
    format: "Chain-specific",
    description: "Native support for TON, TRON, BNB Beacon, and 15+ Cosmos appchains.",
    assets: "ATOM, TON, TRX+",
  },
  {
    name: "Bitcoin",
    logo: "/bitcoin-btc-logo.svg",
    color: "text-orange-600",
    bg: "bg-slate-50",
    border: "border-orange-100",
    format: "bc1, 1, or 3 prefix",
    description: "Native UTXO tracking plus Hiro API indexing for BRC-20 and Runes.",
    assets: "BTC, BRC-20, Runes",
  },
];

export function SupportedNetworks() {
  return (
    <section className="w-full max-w-6xl mt-24 mb-12">
      <div className="flex items-center gap-3 mb-10 px-4">
        <div className="w-10 h-10 rounded-xl bg-brand-100 flex items-center justify-center shadow-sm">
          <Info className="w-5 h-5 text-brand-600" />
        </div>
        <div>
          <h2 className="font-sans text-sm font-bold text-gray-900 uppercase tracking-widest">
            Supported Ecosystems
          </h2>
          <p className="font-sans text-xs text-gray-500 font-medium mt-1">
            ChainWatch uses high-fidelity RPCs and indexing APIs to scan these formats:
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 px-4 font-sans">
        {networks.map((net, i) => (
          <motion.div
            key={net.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * i }}
            whileHover={{ y: -5, transition: { duration: 0.2 } }}
            className="glass-panel p-5 flex flex-col h-full group hover:shadow-xl hover:border-brand-200/50 transition-all"
          >
            <div className="flex items-start justify-between mb-5">
              <div className={cn("w-12 h-12 flex items-center justify-center rounded-2xl shadow-inner transition-transform group-hover:scale-110 duration-300 bg-white border border-gray-100 p-2")}>
                {net.logo ? (
                  <img src={net.logo} alt={net.name} className="w-full h-full object-contain" />
                ) : (
                  <Network className={cn("w-6 h-6", net.color)} />
                )}
              </div>
              <div className="text-[9px] font-mono font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100 flex items-center gap-1 shadow-sm">
                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                ACTIVE
              </div>
            </div>

            <div className="space-y-4 flex-grow">
              <div>
                <h3 className="text-sm font-bold text-gray-900 group-hover:text-brand-600 transition-colors">
                  {net.name}
                </h3>
                <p className="text-[11px] text-gray-500 leading-relaxed mt-1.5 font-medium">
                  {net.description}
                </p>
              </div>

              <div className="pt-4 border-t border-gray-100/60 space-y-3">
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider">Address Format</span>
                  <code className="text-[10px] bg-gray-50 text-gray-700 px-2.5 py-1.5 rounded-lg border border-gray-200/50 font-mono inline-block w-fit whitespace-nowrap overflow-hidden text-ellipsis max-w-full">
                    {net.format}
                  </code>
                </div>
                <div className="flex flex-col gap-1.5">
                  <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider">Detects</span>
                  <span className="text-[10px] text-gray-700 font-semibold bg-white/50 px-2 py-0.5 rounded-md border border-gray-100 inline-block w-fit">
                    {net.assets}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-50 flex items-center justify-between opacity-60 group-hover:opacity-100 transition-opacity">
              <span className="text-[9px] font-bold text-gray-400">
                LATENCY: &lt;200ms
              </span>
              <span className="text-[9px] font-mono text-gray-300">
                L1/L2
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
