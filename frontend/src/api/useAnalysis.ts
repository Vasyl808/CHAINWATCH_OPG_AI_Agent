import { useCallback, useRef } from "react";
import { useAnalysisStore } from "@/store/analysisStore";
import type { SSEEvent } from "@/types";

const VITE_API_URL = import.meta.env.VITE_API_URL || "";
const API_BASE = `${VITE_API_URL}/api/v1`;

export function useAnalysis() {
  const store = useAnalysisStore();
  const esRef = useRef<EventSource | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const startAnalysis = useCallback(
    async (address: string) => {
      // Reset + set address
      store.reset();
      store.setAddress(address);
      store.setPhase("connecting");
      store.addStatus("[SYS] Scanning omnichain portfolio...");

      // Start elapsed timer
      const startMs = Date.now();
      timerRef.current = setInterval(() => {
        store.setElapsed(Date.now() - startMs);
      }, 250);

      try {
        const res = await fetch(`${API_BASE}/analysis/portfolio?address=${encodeURIComponent(address)}`);
        if (!res.ok) throw new Error("Failed to fetch portfolio");
        const data = await res.json();
        const portfolio = data.portfolio || [];
        
        store.setPortfolio(portfolio);
        store.setPhase("selecting");
        store.addStatus(`[OK] Discovered ${portfolio.length} assets. Waiting for user selection.`);
      } catch (err: any) {
        store.setError(err.message || "Failed to fetch portfolio");
        stopTimer();
      }
    },
    [store]
  );

  const startTokenAnalysis = useCallback(
    (token: string, network?: string) => {
      store.setSelectedToken(token);
      store.setPhase("connecting");
      const networkLabel = network ? ` on ${network}` : "";
      store.addStatus(`[SYS] Initializing analysis for ${token}${networkLabel}...`);
      
      const { address } = useAnalysisStore.getState();

      const url = `${API_BASE}/analysis/stream?address=${encodeURIComponent(address)}&token=${encodeURIComponent(token)}${network ? `&network=${encodeURIComponent(network)}` : ""}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.onmessage = (evt) => {
        let event: SSEEvent;
        try {
          event = JSON.parse(evt.data) as SSEEvent;
        } catch {
          return;
        }

        switch (event.type) {
          case "status":
            store.addStatus(event.message ?? "");
            break;

          case "step_start": {
            const n = event.step ?? 1;
            store.startStep(n, event.title);
            store.setPhase(`step${n}` as never);
            store.addStatus(`[RUN] Step ${n}: ${event.title ?? ""}`);
            break;
          }

          case "step_complete":
            store.completeStep(event.step ?? 1);
            break;

          case "tool_call":
            store.addToolCall({
              id: event.call_id ?? String(Date.now()),
              name: event.name ?? "unknown",
              args: event.args ?? {},
            });
            store.addStatus(`[SYS] Calling ${event.name}...`);
            break;

          case "tool_result":
            if (event.call_id) {
              store.updateToolResult(event.call_id, event.content ?? "");
            }
            break;

          case "complete":
            store.setReport(event.report ?? "");
            // Mark all steps complete
            [1, 2, 3, 4].forEach((n) => store.completeStep(n));
            store.addStatus("[OK] Analysis complete");
            stopTimer();
            es.close();
            break;

          case "error":
            store.setError(event.message ?? "Unknown error");
            stopTimer();
            es.close();
            break;

          case "stream_end":
            stopTimer();
            es.close();
            break;
        }
      };

      es.onerror = () => {
        store.setError(
          "Connection to analysis server lost. Ensure the backend is running."
        );
        stopTimer();
        es.close();
      };
    },
    [store]
  );

  const cancel = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    stopTimer();
    store.reset();
  }, [store]);

  return { startAnalysis, startTokenAnalysis, cancel };
}
