import { Cpu, Shield, Zap, Github, Twitter, Disc as Discord } from "lucide-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-gray-200/60 bg-white/50 backdrop-blur-xl relative overflow-hidden">
      {/* Subtle top glare/gradient */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-brand-500/20 to-transparent" />
      
      <div className="max-w-7xl mx-auto px-4 py-8 md:py-12 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
          
          {/* Brand & Copyright */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3 grayscale opacity-80 hover:opacity-100 hover:grayscale-0 transition-all duration-300">
              <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center shadow-sm border border-brand-100">
                <img src="/favicon.svg" alt="ChainWatch Logo" className="w-5 h-5" />
              </div>
              <span className="font-sans text-sm font-bold tracking-wider text-gray-900">
                CHAINWATCH
              </span>
            </div>
            <p className="text-xs text-gray-500 max-w-xs leading-relaxed">
              Decentralized AI monitoring powered by OpenGradient and TEE. Delivering secure and transparent intelligence.
            </p>
            <div className="text-[10px] text-gray-400 font-mono tracking-wider">
              © {currentYear} CHAINWATCH. ALL RIGHTS RESERVED.
            </div>
          </div>

          {/* System Status / Network Metadata (Moved from Header) */}
          <div className="flex flex-col items-center justify-center gap-4">
            <div className="flex items-center gap-6 p-4 rounded-2xl bg-gray-50/50 border border-gray-100/50 shadow-[inset_0_1px_1px_rgba(255,255,255,1)]">
              <div className="flex items-center gap-2 group cursor-help" title="Trusted Execution Environment">
                <Shield className="w-4 h-4 text-brand-500 group-hover:scale-110 transition-transform" />
                <span className="font-mono text-[10px] text-gray-600 font-medium tracking-widest uppercase">
                  TEE Secured
                </span>
              </div>
              
              <div className="w-px h-6 bg-gradient-to-b from-transparent via-gray-300 to-transparent" />
              
              <div className="flex items-center gap-2 group cursor-help" title="Network Version">
                <Zap className="w-4 h-4 text-amber-500 group-hover:scale-110 transition-transform" />
                <span className="font-mono text-[10px] text-gray-600 font-medium tracking-widest uppercase">
                  OpenGradient v0.9
                </span>
              </div>
              
              <div className="w-px h-6 bg-gradient-to-b from-transparent via-gray-300 to-transparent" />
              
              <div className="flex items-center gap-2 group cursor-help" title="Model Intelligence">
                <Cpu className="w-4 h-4 text-emerald-500 group-hover:scale-110 transition-transform" />
                <span className="font-mono text-[10px] text-gray-600 font-medium tracking-widest uppercase">
                  GPT 4.1 2025
                </span>
              </div>
            </div>
          </div>

          {/* Links & Socials */}
          <div className="flex flex-col items-center md:items-end gap-5">
             <div className="flex items-center gap-4">
               <a href="#" className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-400 hover:text-brand-600 hover:border-brand-200 hover:bg-brand-50 transition-all duration-300 hover:scale-110">
                 <Twitter className="w-4 h-4" />
               </a>
               <a href="#" className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-400 hover:text-brand-600 hover:border-brand-200 hover:bg-brand-50 transition-all duration-300 hover:scale-110">
                 <Discord className="w-4 h-4" />
               </a>
               <a href="#" className="w-8 h-8 rounded-full bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-400 hover:text-brand-600 hover:border-brand-200 hover:bg-brand-50 transition-all duration-300 hover:scale-110">
                 <Github className="w-4 h-4" />
               </a>
             </div>
             <div className="flex items-center gap-4 text-xs font-medium tracking-wide">
               <a href="#" className="text-gray-500 hover:text-gray-900 transition-colors">Privacy Policy</a>
               <span className="w-1 h-1 rounded-full bg-gray-300" />
               <a href="#" className="text-gray-500 hover:text-gray-900 transition-colors">Terms</a>
               <span className="w-1 h-1 rounded-full bg-gray-300" />
               <a href="#" className="text-gray-500 hover:text-gray-900 transition-colors">Docs</a>
             </div>
          </div>

        </div>
      </div>
      
      {/* Decorative background blur blobs */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-200/20 rounded-full blur-3xl opacity-50 mix-blend-multiply pointer-events-none transform -translate-y-1/2" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-200/20 rounded-full blur-3xl opacity-50 mix-blend-multiply pointer-events-none transform translate-y-1/4" />
    </footer>
  );
}
