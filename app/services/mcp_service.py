import logging
import asyncio
import time
from app.api.schemas.mcp_schema import (
    ChatRequest, ChatResponse,
)
from app.mcp.client import get_mcp_client
from app.mcp.agent import get_or_create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)

# async def process_chat_request(request: ChatRequest) -> AsyncGenerator[SSEEvent, None]:
#     """
#     Process a chat request with direct agent streaming.
#     Args:
#         request (ChatRequest): The chat request with message and Notion toggle.
#     Yields:
#         SSEEvent: Server-Sent Events for real-time UI updates.
#     """
#     yield SSEEvent(event="agent_start", data=AgentStartData())
    
#     try:
#         if request.enable_notion:
#             logger.info("🧠 Starting full MCP agent mode...")
#             client = await get_mcp_client()
#             agent = create_agent(client)
            
#             # ----  Direct streaming from agent chunks ----
#             final_parts = []  
#             async for chunk in agent.stream(request.message):
#                 logger.debug(f"Agent chunk: {chunk}")
#                 if isinstance(chunk, dict):
#                     #  ---- Parse reasoning from messages ----
#                     messages = chunk.get("messages", [])
#                     for msg in messages:
#                         content_full = msg.get("content", "")
#                         content = content_full.lower()
#                         # ----  Stream reasoning if present ----
#                         if "reasoning" in content or "thought" in content:
#                             thought = content_full.strip()
#                             if thought:
#                                 yield SSEEvent(event="reasoning", data=ReasoningData(thought=thought))
#                         # --- Accumulate assistant outputs as potential final answer parts ---- 
#                         role = (msg.get("role") or "").lower()
#                         if role in {"assistant", "ai", "output"} and content_full:
#                             final_parts.append(content_full.strip())
                    
#                     # ---- Parse tool calls from actions ----
#                     logger.debug(f"Parsing tool calls from chunk actions, chunk: {chunk.get('actions', [])}")
#                     actions = chunk.get("actions", [])
#                     for action in actions:
#                         tool_name = action.get("tool", "unknown")
#                         tool_input = action.get("input", {})
#                         yield SSEEvent(event="tool_call", data=ToolCallData(tool_name=tool_name, tool_input=tool_input))

#                     # ----  Parse tool outputs from steps ----
#                     logger.debug(f"Parsing tool outputs from chunk steps, chunk: {chunk.get('steps', [])}")
#                     steps = chunk.get("steps", [])
#                     for step in steps:
#                         tool_name = step.get("tool", "unknown")
#                         tool_output = str(step.get("output", ""))
#                         yield SSEEvent(event="tool_output", data=ToolOutputData(tool_name=tool_name, tool_output=tool_output))
                    
#                     # ---- Accumulate final output ----
#                     logger.debug(f"Checking for final output in chunk: {chunk}")
#                     if "final_output" in chunk:
#                         final_parts.append(str(chunk["final_output"]))

#             # ----  Yield final answer ----
#             final_answer = " ".join(final_parts).strip()
#             if not final_answer:
#                 try:
#                     final_answer = await agent.run(request.message)
#                 except Exception as e:
#                     logger.warning(f"Fallback run() failed to produce final answer: {e}")
#                     final_answer = "Agent completed successfully."
#             yield SSEEvent(event="final_answer", data=FinalAnswerData(answer=final_answer))
#             logger.info("✅ Full MCP agent mode completed.")
#         else:
#             # ---  Fallback: Basic LLM Call ----
#             logger.info("💬 Using basic LLM mode (Notion disabled)")
#             llm = ChatGoogleGenerativeAI(
#                 model="gemini-2.5-flash",
#                 temperature=0.7,
#             )
#             yield SSEEvent(event="reasoning", data=ReasoningData(thought=f"Processing: {request.message}"))
#             response = await llm.ainvoke(request.message)
#             yield SSEEvent(event="final_answer", data=FinalAnswerData(answer=str(response.content) if getattr(response, "content", None) else "No response generated."))
    
#     except Exception as e:
#         logger.error(f"Error processing request: {e}")
#         yield SSEEvent(event="error", data=ErrorData(error=str(e), error_type=type(e).__name__))
    
#     finally:
#         yield SSEEvent(event="stream_end", data=StreamEndData())


async def process_chat_request_non_stream(request: ChatRequest, timeout_seconds: int = 400) -> ChatResponse:
    """
    Non-streaming version that returns a single JSON response after completion.
    Uses a cached MCPAgent to reduce latency on repeated calls.
    """
    start = time.perf_counter()

    usable_request = f"Page Title: {request.title}\nContents: {request.contents} And return the newly created Notion url/link if successfully created"
    try:
        if request.enable_notion:
            logger.info("🧠 Starting full MCP agent mode (non-stream)...")
            client = await get_mcp_client()
            agent = get_or_create_agent(client)

            async def _run():
                return await agent.run(usable_request)

            # Guard against indefinite hangs
            final_answer = await asyncio.wait_for(_run(), timeout=timeout_seconds)
            print("final_answer:", final_answer)
            latency_ms = int((time.perf_counter() - start) * 1000)
            
            logger.info("✅ Full MCP agent mode completed (non-stream).")
            return ChatResponse(answer=str(final_answer or ""), mode="mcp_agent", latency_ms=latency_ms)
        else:
            logger.info("💬 Using basic LLM mode (non-stream)")
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0.7,
            )
            response = await llm.ainvoke(usable_request)
            latency_ms = int((time.perf_counter() - start) * 1000)
            return ChatResponse(answer=str(response.content) if getattr(response, "content", None) else "No response generated.", mode="basic_llm", latency_ms=latency_ms)
    except asyncio.TimeoutError:
        logger.error("⏱️ MCP agent execution timed out")
        return ChatResponse(answer="Timed out while processing the request.", mode="mcp_agent" if request.enable_notion else "basic_llm", latency_ms=int((time.perf_counter() - start) * 1000))
    except Exception as e:
        logger.error(f"Error processing request (non-stream): {e}")
        return ChatResponse(answer=f"Error: {e}", mode="mcp_agent" if request.enable_notion else "basic_llm", latency_ms=int((time.perf_counter() - start) * 1000))