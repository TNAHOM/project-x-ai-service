from fastapi import FastAPI
from app.api.routers import agent_router
from app.core.logger import setup_logging, get_logger
from app.mcp.client import close_mcp_client, initialize_mcp_client

from contextlib import asynccontextmanager
import asyncio



setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI app started successfully.")
    # ---  Startup ----
    try:
        await initialize_mcp_client()
    except Exception as e:
        # Don't crash the API if MCP backends aren't available; run in degraded mode instead
        logger.error(f"MCP initialization failed at startup: {e}. Continuing without MCP; requests that require MCP will fallback or error gracefully.")
    try:
        yield
    finally:
        logger.info("🛑 FastAPI app shutting down.")
        # ---  Shutdown ----
        try:
            # Best-effort shutdown with timeout; avoid propagating cancellation during reload/Ctrl+C
            await close_mcp_client(timeout=5.0)
        except asyncio.CancelledError:
            logger.warning("⚠️ Lifespan shutdown cancelled during MCP client close; continuing app shutdown.")
        
app = FastAPI(title="AI Agent Microservice", version='1.0', lifespan=lifespan)


app.include_router(agent_router.router, prefix="/agent", tags=["Agent"])
# app.include_router(mcp_router.router, prefix="/mcp", tags=["MCP"])

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Agent Microservice!"}