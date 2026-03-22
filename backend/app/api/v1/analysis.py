from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.schemas import AnalysisRequest
from app.services.agent import stream_analysis
from app.services.agent.pool import get_agent_pool
from app.services.portfolio import fetch_portfolio

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/portfolio")
async def get_wallet_portfolio(
    address: str = Query(..., description="Blockchain wallet address")
):
    """Fetches and returns the wallet's portfolio in JSON format."""
    try:
        req = AnalysisRequest(address=address)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    
    portfolio = await fetch_portfolio(req.address)
    return {"portfolio": portfolio}


@router.get("/stream")
async def stream_wallet_analysis(
    address: str = Query(..., description="Blockchain wallet address"),
    token: str | None = Query(None, description="Specific token to analyze"),
    network: str | None = Query(None, description="Network where the token is held"),
) -> StreamingResponse:
    """
    SSE endpoint - streams wallet analysis events in real time.

    Event types emitted:
    - status      : informational status message
    - step_start  : a new analysis step begins  {step, title}
    - step_complete: step finished
    - tool_call   : agent invokes a tool        {name, args, call_id}
    - tool_result : tool returned a result      {name, content, call_id}
    - complete    : final markdown report       {report}
    - error       : something went wrong        {message}
    - stream_end  : sentinel - close the connection
    """
    try:
        req = AnalysisRequest(address=address)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    private_key = settings.og_private_key
    if not private_key:
        raise HTTPException(
            status_code=503,
            detail="OG_PRIVATE_KEY is not configured on the server.",
        )
        
    pool = get_agent_pool()
    pool_state = pool.get_status()
    if pool_state["queued_agents"] >= settings.max_queue_depth:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Server is currently overloaded. Please try again later.",
            headers={"Retry-After": "30"}
        )

    return StreamingResponse(
        stream_analysis(req.address, private_key, token, network),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/status")
async def get_queue_status():
    """Returns the current agent pool concurrency and queue state."""
    private_key = settings.og_private_key
    if not private_key:
        return {"status": "unconfigured"}
        
    pool = get_agent_pool()
    return pool.get_status()
