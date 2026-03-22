import { motion } from "framer-motion";
import { shortenAddress } from "@/utils";
import { Monitor, BarChart3, Bot } from "lucide-react";

interface Props {
  address: string;
  phase: string;
}

const PHASE_LABELS: Record<string, string> = {
  connecting: "Connecting to Secure Enclave",
  step1: "Discovering Asset Topology",
  step2: "Analyzing Yield Protocols",
  step3: "Running Security Audit",
  step4: "Generating Intelligence Report",
  complete: "Analysis Complete",
};

export function ScanningVisual({ address, phase }: Props) {
  const label = PHASE_LABELS[phase] ?? "Processing Data...";

  return (
    <div className="flex flex-col items-center gap-7 py-8">
      {/* Sleek Workspace Scene */}
      <div className="relative w-64 h-32 flex items-center justify-center border-b-2 border-dashed border-gray-200 mt-4 mb-2">
        {/* Left: Computer/Terminal */}
        <div className="absolute left-0 bottom-0 flex flex-col items-center">
          <Monitor className="w-10 h-10 text-brand-500 mb-1" strokeWidth={1.5} />
          <div className="w-12 h-2 bg-gray-200 rounded-full" />
        </div>

        {/* Right: Charts/Board */}
        <div className="absolute right-0 bottom-0 flex flex-col items-center">
          <BarChart3 className="w-10 h-10 text-emerald-500 mb-1" strokeWidth={1.5} />
          <div className="w-12 h-2 bg-gray-200 rounded-full" />
        </div>

        {/* Agent running back and forth */}
        <motion.div
          className="absolute bottom-1 z-10"
          animate={{
            x: [-80, -80, 80, 80, -80], // left to right sequence
            scaleX: [1, -1, -1, 1, 1], // flip direction depending on movement
            y: [0, -10, 0, -10, 0, -10, 0, -10, 0] // bounce effect
          }}
          transition={{
            duration: 4,
            repeat: Infinity,
            times: [0, 0.2, 0.5, 0.7, 1],
            ease: "easeInOut"
          }}
        >
          <div className="relative">
            <Bot className="w-12 h-12 text-brand-600 drop-shadow-md bg-white rounded-full p-1" strokeWidth={1.5} />
            {/* cute thinking dots above agent */}
            <motion.div 
              className="absolute -top-4 left-1/2 -translate-x-1/2 text-brand-400 font-bold"
              animate={{ opacity: [0, 1, 0] }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              ...
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* Dynamic text and timer */}
      <div className="text-center space-y-2">
        <motion.h3
          key={label}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-sans text-sm font-bold tracking-wide text-gray-900 uppercase"
        >
          {label}
        </motion.h3>
        <p className="font-mono text-xs text-brand-600 bg-brand-50 px-2 py-1 rounded inline-block">
          {shortenAddress(address, 12)}
        </p>
      </div>

      <div className="w-full space-y-2 px-6">
        {[0.6, 0.8, 0.4].map((w, i) => (
          <div key={i} className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
             <motion.div 
               className="h-full bg-brand-400 rounded-full"
               initial={{ width: "0%" }}
               animate={{ width: `${w * 100}%` }}
               transition={{ duration: 1 + i*0.5, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" }}
             />
          </div>
        ))}
      </div>
    </div>
  );
}
