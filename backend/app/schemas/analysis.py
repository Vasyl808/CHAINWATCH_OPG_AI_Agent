from pydantic import BaseModel, field_validator
import re


class AnalysisRequest(BaseModel):
    address: str

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Wallet address cannot be empty")
        # EVM (0x + 40 hex)
        if re.match(r"^0x[0-9a-fA-F]{40}$", v):
            return v
        # SUI (0x + 64 hex)
        if re.match(r"^0x[0-9a-fA-F]{64}$", v):
            return v
        # Solana (base58, 32-44 chars)
        if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", v):
            return v
        # Bitcoin (bc1, 1..., 3...)
        if re.match(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$", v):
            return v
        raise ValueError("Unrecognized wallet address format")


class SSEEvent(BaseModel):
    type: str
    data: dict = {}
