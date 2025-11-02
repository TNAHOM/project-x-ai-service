import logging
import asyncio
from typing import Optional
from mcp_use import MCPClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Get Global Singleton for the MCPClient --- 
_client_instance: Optional[MCPClient] = None 

async def get_mcp_client() -> MCPClient:
    """
        Get the Singleton MCPClient instance . 
    """
    global _client_instance
    if _client_instance is None:
        raise RuntimeError("MCP client not initialized. Call init_mcp_client() first.")
    return _client_instance

async def initialize_mcp_client() -> MCPClient:
    """
        Initialize the singleton MCPClient from config. 
    """
    global _client_instance

    if _client_instance is not None:
        logger.warning("MCPClient already initialized. Skipping.")
        return _client_instance
    logger.info("🚀 Initializing MCPClient...")
    try:
        # --- Create Client form Config file --- 
        client = MCPClient.from_config_file(settings.mcp_config_path)
        # --- Health Check : Create All Sessions --- 
        await client.create_all_sessions()
        # --- Store as singleton --- *
        _client_instance = client
        logger.info("✅ MCPClient initialized and sessions created successfully.")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize MCPClient: {e}")
        raise RuntimeError(f"MCPClient initialization failed: {e}")
    
    
async def close_mcp_client(timeout: float = 5.0) -> None:
    """
    Gracefully close the MCPClient sessions.
    This should be called during app shutdown.
    """
    global _client_instance
    
    if _client_instance is None:
        logger.warning("MCPClient not initialized. Nothing to close.")
        return
    
    logger.info("🛑 Closing MCPClient sessions...")
    try:
        # Shield against cancellation and bound the waiting time
        await asyncio.wait_for(asyncio.shield(_client_instance.close_all_sessions()), timeout=timeout)
        logger.info("✅ MCPClient sessions closed successfully.")
    except asyncio.TimeoutError:
        logger.warning("⌛ Timeout while closing MCPClient sessions; proceeding with shutdown.")
    except asyncio.CancelledError:
        # Swallow cancellation to allow graceful app shutdown
        logger.warning("⚠️ Shutdown cancelled during MCPClient close; proceeding with best-effort cleanup.")
    except Exception as e:
        logger.error(f"❌ Error closing MCPClient: {e}")
    finally:
        _client_instance = None