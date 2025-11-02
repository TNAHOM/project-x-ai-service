from fastapi import APIRouter
from app.api.schemas.mcp_schema import ChatRequest, ChatResponse
from app.core.logger import get_logger
from app.services.mcp_service import process_chat_request_non_stream


logger = get_logger(__name__)
router = APIRouter()

@router.post("/stream", response_model=ChatResponse)
async def notion_mcp_tool(request: ChatRequest):
    logger.info("Received chat request (non-stream)")
    """
    - message: User's natural language query.
    - enable_notion: Toggle Notion MCP integration (default: true).

    Returns a single JSON response after processing completes.
    """
    response = await process_chat_request_non_stream(request)
    return response