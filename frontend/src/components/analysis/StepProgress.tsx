import { motion } from "framer-motion";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import type { StepInfo } from "@/types";
import { cn } from "@/utils";

interface Props {
  steps: StepInfo[];
}

export function StepProgress({ steps }: Props) {
  return (
    <div className="space-y-3 px-2">
      {steps.map((step, i) => (
        <motion.div
          key={step.number}
          initial={{ opacity: 0, x: -16 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.3 }}
          className={cn(
            "flex items-center gap-4 transition-all duration-300",
            step.status === "pending" && "opacity-50"
          )}
        >
          {/* Icon */}
          <div className="shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-slate-50 border border-slate-100 shadow-sm relative z-10">
            {step.status === "complete" && (
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            )}
            {step.status === "active" && (
              <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
            )}
            {step.status === "pending" && (
              <Circle className="w-3 h-3 text-slate-300" />
            )}
          </div>

          {/* Step info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "font-sans text-[10px] font-bold tracking-wider uppercase",
                  step.status === "active" && "text-brand-600",
                  step.status === "complete" && "text-emerald-600",
                  step.status === "pending" && "text-slate-400"
                )}
              >
                Step {step.number}
              </span>
            </div>
            <p
              className={cn(
                "font-sans text-sm font-medium truncate",
                step.status === "active" && "text-gray-900",
                step.status === "complete" && "text-gray-600",
                step.status === "pending" && "text-slate-400"
              )}
            >
              {step.title}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
