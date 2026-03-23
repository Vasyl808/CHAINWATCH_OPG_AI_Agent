from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    og_private_key: str = ""
    frontend_origin: str = "http://localhost:5173"
    app_title: str = "ChainWatch API"
    app_version: str = "1.0.0"

    max_concurrent_agents: int = 5
    max_queue_depth: int = 20
    agent_timeout_seconds: int = 600

    og_model_cid: str = "anthropic/claude-4.0-sonnet"
    og_llm_max_tokens: int = 4096
    og_opg_approval_amount: int = 10

    og_agent_address: str = "0xEaD1B6dF9F22E5b697d802873dfd36401855b0a1"
    faucet_interval_seconds: int = 18300
    faucet_url: str = "https://faucet.opengradient.ai/api/claim"

    # ── Public endpoints (no key needed) ─────────────────────────────────────
    sol_rpc_url: str = "https://api.mainnet-beta.solana.com"
    sui_rpc_url: str = "https://fullnode.mainnet.sui.io:443"
    ankr_rpc_url: str = "https://rpc.ankr.com/multichain"
    hyperliquid_api_url: str = "https://api.hyperliquid.xyz/info"
    defillama_yields_url: str = "https://yields.llama.fi/pools"
    jupiter_token_list_url: str = "https://token.jup.ag/strict"

    # ── Covalent GoldRush ─────────────────────────────────────────────────────
    # Free plan: 100k credits/month, no credit card.
    # Register at: https://goldrush.dev
    # Used for: ERC-20 token balances across 200+ EVM chains.
    # Without this key: only native coin balances are fetched for EVM chains.
    covalent_api_key: str = ""


settings = Settings()