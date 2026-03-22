import { Cpu, Wifi } from "lucide-react";
import { useAnalysisStore } from "@/store/analysisStore";

export function Header() {
  const reset = useAnalysisStore((s) => s.reset);

  const handleGoHome = () => {
    reset();
  };

  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-gray-200/60 bg-white/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <button
          onClick={handleGoHome}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
        >
          <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center shadow-sm border border-brand-100">
            <img src="/favicon.svg" alt="ChainWatch Logo" className="w-5 h-5" />
          </div>
          <span className="font-sans text-sm font-bold tracking-wider text-gray-900">
            CHAINWATCH
          </span>
        </button>

        {/* Center space */}
        <div className="hidden md:flex flex-1"></div>

        {/* Status indicators */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse-soft" />
            <span className="font-sans text-[11px] font-semibold text-gray-600 tracking-wide uppercase">System Online</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-400">
            <Cpu className="w-3.5 h-3.5" />
            <span className="font-mono text-[10px] font-medium hidden sm:block">TEE</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-400">
            <Wifi className="w-3.5 h-3.5" />
            <span className="font-mono text-[10px] font-medium hidden sm:block">SSE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
