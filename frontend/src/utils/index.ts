export function formatElapsed(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s % 60}s`;
}

export function shortenAddress(addr: string, chars = 6): string {
  if (addr.length <= chars * 2 + 3) return addr;
  return `${addr.slice(0, chars)}...${addr.slice(-chars)}`;
}

export function detectChain(address: string): string {
  if (/^0x[0-9a-fA-F]{64}$/.test(address)) return "SUI";
  if (/^0x[0-9a-fA-F]{40}$/.test(address)) return "EVM";
  if (/^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(address)) return "SOL";
  if (/^(bc1|[13])/.test(address)) return "BTC";
  return "UNKNOWN";
}

export function formatToolName(name: string): string {
  const map: Record<string, string> = {
    get_omnichain_balance: "Balance Fetch",
    get_defi_yields: "DeFi Yields",
    search_crypto_news: "Security Search",
  };
  return map[name] ?? name;
}

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
