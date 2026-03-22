import asyncio
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def auto_faucet_task():
    """Background task to claim tokens from the faucet periodically."""
    # Ensure there is an address configured
    if not settings.og_agent_address:
        logger.warning("No og_agent_address configured. Auto-faucet task will exit.")
        return

    logger.info(f"Starting auto-faucet task for {settings.og_agent_address} every {settings.faucet_interval_seconds} seconds.")

    # We use a while True loop to run this continuously
    while True:
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Requesting tokens from faucet for {settings.og_agent_address}...")
                response = await client.post(
                    settings.faucet_url,
                    json={"address": settings.og_agent_address},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Faucet claim successful: {data}")
                elif response.status_code == 429:
                    # Rate limit exceeded
                    data = response.json()
                    if isinstance(data, dict) and "msg" in data:
                        logger.warning(f"Faucet rate limit: {data['msg']}")
                    else:
                        logger.warning(f"Faucet rate limit: {response.text}")
                else:
                    logger.error(f"Faucet request failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error in auto_faucet_task: {e}")
        
        # Sleep for the configured interval before the next request
        await asyncio.sleep(settings.faucet_interval_seconds)
