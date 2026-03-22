import { type ReactNode } from "react";
import { cn } from "@/utils";

interface Props {
  children: ReactNode;
  className?: string;
  label?: string;
  accent?: "cyan" | "pink" | "purple" | "gold"; // Legacy prop, we can map them to nice colors
  scanlines?: boolean; // Unused now
}

const ACCENT_COLORS = {
  cyan: "bg-brand-50 text-brand-700 border-brand-100",
  pink: "bg-rose-50 text-rose-700 border-rose-100",
  purple: "bg-violet-50 text-violet-700 border-violet-100",
  gold: "bg-amber-50 text-amber-700 border-amber-100",
} as const;

export function CyberPanel({
  children,
  className,
  label,
  accent = "cyan",
}: Props) {
  return (
    <div className={cn("glass-panel pt-8", className)}>
      {label && (
        <div
          className={cn(
            "absolute top-0 left-0 w-full px-4 py-2 border-b",
            "font-sans text-xs font-semibold tracking-wide uppercase",
            ACCENT_COLORS[accent]
          )}
        >
          {label}
        </div>
      )}
      {children}
    </div>
  );
}
