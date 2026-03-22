from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    og_key_configured: bool
