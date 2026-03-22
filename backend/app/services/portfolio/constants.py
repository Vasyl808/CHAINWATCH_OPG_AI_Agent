"""Chain configs, stablecoin sets, spam patterns, CoinGecko symbol mappings."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# EVM chains
# (display_name, covalent_chain_id, native_symbol, native_rpc)
# ---------------------------------------------------------------------------
EVM_CHAINS: list[tuple[str, str, str, str]] = [
    ("Ethereum",          "eth-mainnet",            "ETH",   "https://eth.llamarpc.com"),
    ("Arbitrum One",      "arbitrum-mainnet",        "ETH",   "https://arb1.arbitrum.io/rpc"),
    ("Optimism",          "optimism-mainnet",        "ETH",   "https://mainnet.optimism.io"),
    ("Base",              "base-mainnet",            "ETH",   "https://mainnet.base.org"),
    ("Blast",             "blast-mainnet",           "ETH",   "https://rpc.blast.io"),
    ("Linea",             "linea-mainnet",           "ETH",   "https://rpc.linea.build"),
    ("Scroll",            "scroll-mainnet",          "ETH",   "https://rpc.scroll.io"),
    ("zkSync Era",        "zksync-mainnet",          "ETH",   "https://mainnet.era.zksync.io"),
    ("Polygon zkEVM",     "polygon-zkevm-mainnet",   "ETH",   "https://zkevm-rpc.com"),
    ("Mantle",            "mantle-mainnet",          "MNT",   "https://rpc.mantle.xyz"),
    ("Mode",              "mode-mainnet",            "ETH",   "https://mainnet.mode.network"),
    ("Zora",              "zora-mainnet",            "ETH",   "https://rpc.zora.energy"),
    ("Polygon",           "matic-mainnet",           "POL",   "https://polygon-rpc.com"),
    ("BNB Chain",         "bsc-mainnet",             "BNB",   "https://bsc-dataseed.binance.org"),
    ("opBNB",             "opbnb-mainnet",           "BNB",   "https://opbnb-mainnet-rpc.bnbchain.org"),
    ("Avalanche C-Chain", "avalanche-mainnet",       "AVAX",  "https://api.avax.network/ext/bc/C/rpc"),
    ("Fantom",            "fantom-mainnet",          "FTM",   "https://rpc.ftm.tools"),
    ("Sonic",             "sonic-mainnet",           "S",     "https://rpc.soniclabs.com"),
    ("Gnosis",            "gnosis-mainnet",          "xDAI",  "https://rpc.gnosischain.com"),
    ("Celo",              "celo-mainnet",            "CELO",  "https://forno.celo.org"),
    ("Cronos",            "cronos-mainnet",          "CRO",   "https://evm.cronos.org"),
    ("Moonbeam",          "moonbeam-mainnet",        "GLMR",  "https://rpc.api.moonbeam.network"),
    ("Moonriver",         "moonriver-mainnet",       "MOVR",  "https://rpc.api.moonriver.moonbeam.network"),
    ("Metis",             "metis-mainnet",           "METIS", "https://andromeda.metis.io/?owner=1088"),
    ("Klaytn",            "klaytn-mainnet",          "KLAY",  "https://public-node-api.klaytnapi.com/v1/cypress"),
    ("Aurora",            "aurora-mainnet",          "ETH",   "https://mainnet.aurora.dev"),
    ("Harmony",           "harmony-mainnet",         "ONE",   "https://api.harmony.one"),
    ("Kava EVM",          "kava-mainnet",            "KAVA",  "https://evm.kava.io"),
    ("Fuse",              "fuse-mainnet",            "FUSE",  "https://rpc.fuse.io"),
    ("Evmos",             "evmos-mainnet",           "EVMOS", "https://eth.bd.evmos.org:8545"),
    ("Boba",              "boba-mainnet",            "ETH",   "https://mainnet.boba.network"),
    ("Taiko",             "taiko-mainnet",           "ETH",   "https://rpc.mainnet.taiko.xyz"),
]

# ---------------------------------------------------------------------------
# Cosmos chains  (prefix, chain_id, native_symbol, native_exponent)
# ---------------------------------------------------------------------------
COSMOS_CHAINS: list[tuple[str, str, str, int]] = [
    ("cosmos1",  "cosmoshub", "ATOM",  6),
    ("osmo1",    "osmosis",   "OSMO",  6),
    ("juno1",    "juno",      "JUNO",  6),
    ("stars1",   "stargaze",  "STARS", 6),
    ("axelar1",  "axelar",    "AXL",   6),
    ("inj1",     "injective", "INJ",   18),
    ("sei1",     "sei",       "SEI",   6),
    ("strd1",    "stride",    "STRD",  6),
    ("dydx1",    "dydx",      "DYDX",  18),
    ("noble1",   "noble",     "USDC",  6),
    ("neutron1", "neutron",   "NTRN",  6),
    ("archway1", "archway",   "ARCH",  18),
    ("umee1",    "umee",      "UMEE",  6),
    ("kava1",    "kava",      "KAVA",  6),
    ("evmos1",   "evmos",     "EVMOS", 18),
]

# ---------------------------------------------------------------------------
# Starknet known tokens
# ---------------------------------------------------------------------------
STARKNET_TOKENS: list[tuple[str, str, int]] = [
    ("0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7", "ETH",  18),
    ("0x053c91253bc9682c04929ca02ed00b3e423f6710d2ee7e0d5ebb06f3ecf368a8", "USDC",  6),
    ("0x068f5c6a61780768455de69077e07e89787839bf8166decfbf92b645209c0fb8", "USDT",  6),
    ("0x00da114221cb83fa859dbdb4c44beeaa0bb37c7537ad5ae66fe5e0efd20e6eb3", "DAI",  18),
    ("0x042b8f0484674ca266ac5d08e4ac6a3fe65bd3129795def2dca5c34ecc5f96d2", "wBTC",  8),
    ("0x04718f5a0fc34cc1af16a1cdee98ffb20c31f5cd61d6ab07201858f4287c938d", "STRK", 18),
]
STARKNET_BALANCE_SELECTOR = "0x2e4263afad30923c891518314c3c95dbe830a16874e8abc5777a9a20b54c76e"

# ---------------------------------------------------------------------------
# USD price mappings
# ---------------------------------------------------------------------------
SYMBOL_TO_COINGECKO_ID: dict[str, str] = {
    "ETH":   "ethereum",
    "BTC":   "bitcoin",
    "SOL":   "solana",
    "SUI":   "sui",
    "BNB":   "binancecoin",
    "AVAX":  "avalanche-2",
    "FTM":   "fantom",
    "CELO":  "celo",
    "CRO":   "crypto-com-chain",
    "KAVA":  "kava",
    "METIS": "metis-token",
    "GLMR":  "moonbeam",
    "MOVR":  "moonriver",
    "ONE":   "harmony",
    "FUSE":  "fuse-network-token",
    "KLAY":  "klay-token",
    "EVMOS": "evmos",
    "MNT":   "mantle",
    "S":     "sonic-3",
    "POL":   "polygon-ecosystem-token",
    "TRX":   "tron",
    "TON":   "the-open-network",
    "ATOM":  "cosmos",
    "OSMO":  "osmosis",
    "JUNO":  "juno-network",
    "STARS": "stargaze",
    "AXL":   "axelar",
    "INJ":   "injective-protocol",
    "SEI":   "sei-network",
    "DYDX":  "dydx",
    "STRK":  "starknet",
    "NTRN":  "neutron",
    "ARCH":  "archway",
}

STABLECOINS: set[str] = {
    "USDC", "USDT", "DAI", "BUSD", "TUSD", "FRAX", "LUSD",
    "UUSD", "cUSD", "USDD", "USDJ", "USDP", "GUSD", "USD",
}

SPAM_PATTERN = re.compile(
    r'[\u200b\u200c\u200d\u2060\u2061\u2062\u2063\u2064\u2065'
    r'\u2066\u2067\u2068\u2069\u206a\u206b\u206c\u206d\u206e'
    r'\u206f\ufeff\u00ad]'
)

# ---------------------------------------------------------------------------
# DefiLlama yields network aliases
# ---------------------------------------------------------------------------
NETWORK_ALIASES: dict[str, str] = {
    "eth": "ethereum", "ethereum": "ethereum",
    "arb": "arbitrum", "arbitrum": "arbitrum", "arbitrum one": "arbitrum",
    "op": "optimism", "optimism": "optimism",
    "base": "base",
    "matic": "polygon", "polygon": "polygon",
    "bnb": "bsc", "bsc": "bsc", "bnb chain": "bsc",
    "avax": "avalanche", "avalanche": "avalanche",
    "ftm": "fantom", "fantom": "fantom",
    "linea": "linea", "scroll": "scroll",
    "zksync": "zksync era", "zksync era": "zksync era",
    "mantle": "mantle", "celo": "celo", "gnosis": "gnosis",
    "cronos": "cronos", "moonbeam": "moonbeam", "moonriver": "moonriver",
    "kava": "kava", "fuse": "fuse", "harmony": "harmony", "aurora": "aurora",
    "blast": "blast", "mode": "mode", "zora": "zora",
    "sonic": "sonic", "taiko": "taiko",
    "sol": "solana", "solana": "solana",
    "sui": "sui",
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "ton": "ton",
    "trx": "tron", "tron": "tron",
    "atom": "cosmos", "cosmos": "cosmos",
    "osmo": "osmosis", "osmosis": "osmosis",
    "starknet": "starknet", "strk": "starknet",
    "inj": "injective", "injective": "injective",
    "sei": "sei", "dydx": "dydx",
    "arch": "archway", "ntrn": "neutron", "neutron": "neutron",
    "hbar": "hedera", "hedera": "hedera",
    "near": "near",
    "ftt": "fantom",
}
