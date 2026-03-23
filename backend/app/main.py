import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.services.faucet import auto_faucet_task
from app.services.registry import init_registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    print(f"ChainWatch API v{settings.app_version} starting up")
    print(f"OG key configured: {bool(settings.og_private_key)}")

    # Initialize the service registry (HTTP client, caches, agent pool)
    registry = init_registry(
        private_key=settings.og_private_key,
        max_concurrent=settings.max_concurrent_agents,
    )

    # Start background auto-faucet task
    faucet_task = asyncio.create_task(auto_faucet_task())

    yield

    print("ChainWatch API shutting down")
    faucet_task.cancel()
    try:
        await faucet_task
    except asyncio.CancelledError:
        pass
    await registry.shutdown()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Blockchain wallet security analysis powered by OpenGradient TEE LLM",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chainwatch-ai-agent.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", include_in_schema=False)
async def root():
    return {"service": settings.app_title, "version": settings.app_version, "docs": "/docs"}
