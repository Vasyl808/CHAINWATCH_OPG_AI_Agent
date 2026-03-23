import { create } from "zustand";
import type {
  AnalysisState,
  AnalysisPhase,
  PortfolioToken,
  StepInfo,
  ToolCallEntry,
} from "@/types";

const DEFAULT_STEPS: StepInfo[] = [
  { number: 1, title: "Portfolio Discovery", status: "pending" },
  { number: 2, title: "Yield Analysis", status: "pending" },
  { number: 3, title: "Security Audit", status: "pending" },
  { number: 4, title: "Risk Assessment & Report", status: "pending" },
];

interface AnalysisStore extends AnalysisState {
  setAddress: (address: string) => void;
  setPortfolio: (portfolio: PortfolioToken[]) => void;
  setSelectedToken: (token: string | null) => void;
  setPhase: (phase: AnalysisPhase) => void;
  startStep: (stepNumber: number, title?: string) => void;
  completeStep: (stepNumber: number) => void;
  addToolCall: (entry: Omit<ToolCallEntry, "timestamp">) => void;
  updateToolResult: (callId: string, result: string) => void;
  addStatus: (message: string) => void;
  setReport: (report: string) => void;
  setError: (error: string) => void;
  setElapsed: (ms: number) => void;
  reset: () => void;
  resetForNewToken: () => void;
}

const initialState: AnalysisState = {
  phase: "idle",
  address: "",
  steps: DEFAULT_STEPS,
  toolCalls: [],
  statusMessages: [],
  portfolio: [],
  selectedToken: null,
  report: null,
  error: null,
  startedAt: null,
  elapsedMs: 0,
};

export const useAnalysisStore = create<AnalysisStore>((set) => ({
  ...initialState,

  setAddress: (address) => set({ address }),
  
  setPortfolio: (portfolio) => set({ portfolio }),
  
  setSelectedToken: (selectedToken) => set({ selectedToken }),

  setPhase: (phase) =>
    set((s) => ({
      phase,
      startedAt: phase === "connecting" ? Date.now() : s.startedAt,
    })),

  startStep: (stepNumber, title) =>
    set((s) => ({
      steps: s.steps.map((step) =>
        step.number === stepNumber
          ? {
              ...step,
              status: "active",
              title: title ?? step.title,
              startedAt: Date.now(),
            }
          : step
      ),
    })),

  completeStep: (stepNumber) =>
    set((s) => ({
      steps: s.steps.map((step) =>
        step.number === stepNumber
          ? { ...step, status: "complete", completedAt: Date.now() }
          : step
      ),
    })),

  addToolCall: (entry) =>
    set((s) => ({
      toolCalls: [
        ...s.toolCalls,
        { ...entry, timestamp: Date.now() },
      ],
    })),

  updateToolResult: (callId, result) =>
    set((s) => ({
      toolCalls: s.toolCalls.map((tc) =>
        tc.id === callId ? { ...tc, result } : tc
      ),
    })),

  addStatus: (message) =>
    set((s) => ({
      statusMessages: [...s.statusMessages.slice(-19), message],
    })),

  setReport: (report) =>
    set({
      report,
      phase: "complete",
    }),

  setError: (error) => set({ error, phase: "error" }),

  setElapsed: (ms) => set({ elapsedMs: ms }),

  reset: () => set({ ...initialState, steps: DEFAULT_STEPS.map((s) => ({ ...s })) }),

  resetForNewToken: () => set(() => ({
    phase: "selecting",
    steps: DEFAULT_STEPS.map((step) => ({ ...step })),
    toolCalls: [],
    statusMessages: [],
    selectedToken: null,
    report: null,
    error: null,
    startedAt: null,
    elapsedMs: 0,
  })),
}));
