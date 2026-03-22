import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, ChevronRight, Settings } from "lucide-react";

interface Props {
  messages: string[];
  maxHeight?: string;
}

export function TerminalLog({ messages, maxHeight = "300px" }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    const isNearBottom = distanceFromBottom < 48;
    if (isNearBottom) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={containerRef}
      className="font-mono text-xs overflow-y-auto px-4 pb-4"
      style={{ maxHeight, scrollbarWidth: "thin" }}
    >
      <AnimatePresence initial={false}>
        {messages.map((msg, i) => {
          const isSuccess = msg.startsWith("[OK]");
          const isProgress = msg.startsWith("[RUN]");
          const isSetting = msg.startsWith("[SYS]");
          
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="py-1.5 flex gap-3 items-start border-b border-gray-100 last:border-0"
            >
              <div className="mt-0.5">
                {isSuccess ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                ) : isProgress ? (
                  <ChevronRight className="w-3.5 h-3.5 text-brand-500" />
                ) : isSetting ? (
                  <Settings className="w-3.5 h-3.5 text-amber-500 animate-spin-slow" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-300 block ml-1 mt-1" />
                )}
              </div>
              
              <span className="text-gray-600 leading-relaxed break-words flex-1">
                {msg.replace(/^\[(OK|RUN|SYS|ERR)\]\s*/, "")}
              </span>
            </motion.div>
          );
        })}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
