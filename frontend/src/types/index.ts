export type AnalysisPhase =
  | "idle"
  | "connecting"
  | "selecting"
  | "step1"
  | "step2"
  | "step3"
  | "step4"
  | "complete"
  | "error";

export interface PortfolioToken {
  symbol: string;
  amount: number;
  usd_value: number;
  network: string;
}

export interface StepInfo {
  number: number;
  title: string;
  status: "pending" | "active" | "complete";
  startedAt?: number;
  completedAt?: number;
}

export type SSEEventType =
  | "status"
  | "step_start"
  | "step_complete"
  | "tool_call"
  | "tool_result"
  | "complete"
  | "error"
  | "stream_end";

export interface SSEEvent {
  type: SSEEventType;
  message?: string;
  step?: number;
  title?: string;
  name?: string;
  args?: Record<string, unknown>;
  call_id?: string;
  content?: string;
  report?: string;
}

export interface ToolCallEntry {
  id: string;
  name: string;
  args: Record<string, unknown>;
  result?: string;
  timestamp: number;
}

export interface AnalysisState {
  phase: AnalysisPhase;
  address: string;
  steps: StepInfo[];
  toolCalls: ToolCallEntry[];
  statusMessages: string[];
  portfolio: PortfolioToken[];
  selectedToken: string | null;
  report: string | null;
  error: string | null;
  startedAt: number | null;
  elapsedMs: number;
}
