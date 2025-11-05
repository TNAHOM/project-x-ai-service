
from math import log
from langchain_google_genai import ChatGoogleGenerativeAI
from app.api.schemas.mcp_schema import ChatRequest
from app.core.config import settings
from app.core.logger import get_logger
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from app.mcp.notion.tools import create_notion_page, create_google_doc
from app.mcp.client import get_mcp_client
from app.mcp.agent import MCPAgent


logger = get_logger(__name__)

class ExecutionAgentService:
    def __init__(self) -> None:
        api_key = getattr(settings, "GOOGLE_API_KEY", None)
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the configuration.")
        self.api_key = api_key

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            max_tokens=None,
            timeout=300,
            max_retries=2,
        )

    async def run_agent(self, messageRequest: ChatRequest, response_schema=None):
        """
        Run the agent using ChatGoogleGenerativeAI.bind_tools().
        """

        client = await get_mcp_client()
        if client is not None:
            agent = MCPAgent(llm=self.llm, client=client)
            result = await agent.run("what tools do you have?")
            logger.info(result)
            return {"message": result}

        else:
            return {"message": "don't have tools!"}
        # try:
        #     # Expose both Notion and Google Docs/Sheets tools; the model will pick the right one
        #     tools = [create_notion_page, create_google_doc]
        #     if isinstance(tools, dict) and "error" in tools:
        #         return tools
        #     if not isinstance(tools, list):
        #         return {"error": "MCP tools are not in a valid list format."}
        #     llm = ChatGoogleGenerativeAI(
        #         model="gemini-2.5-flash",
        #         temperature=0,
        #         max_tokens=None,
        #         timeout=300,
        #         max_retries=2,
        #     )
        #     # Bind tools first (tools + LLM)
        #     llm_with_tools = llm.bind_tools(tools)

        #     # Normalize incoming request into LangChain message objects
        #     messages = []
        #     if isinstance(messageRequest, list):
        #         # Expect list of {role, content}
        #         for m in messageRequest:
        #             role = m.get("role") if isinstance(m, dict) else None
        #             content = m.get("content") if isinstance(m, dict) else str(m)
        #             if role == "system":
        #                 messages.append(SystemMessage(content=content))
        #             else:
        #                 messages.append(HumanMessage(content=content))
        #     else:
        #         messages = [HumanMessage(content=str(messageRequest))]

        #     # First model invocation
        #     ai_msg = llm_with_tools.invoke(messages)

        #     # If there are tool calls, execute them and send results back once
        #     tool_calls = getattr(ai_msg, "tool_calls", []) or []
        #     if tool_calls:
        #         tool_map = {t.name: t for t in tools if hasattr(t, "name")}
        #         tool_msgs = []
        #         for call in tool_calls:
        #             name = call.get("name")
        #             args = call.get("args", {})
        #             call_id = call.get("id")
        #             tool = tool_map.get(name)
        #             if not tool:
        #                 result = f"Tool '{name}' not found."
        #             else:
        #                 try:
        #                     # Normalize args to match tool signature
        #                     if isinstance(args, dict):
        #                         if "request" in args:
        #                             req_value = args["request"]
        #                             if isinstance(req_value, dict):
        #                                 args = {"request": ChatRequest(**req_value)}
        #                             elif isinstance(req_value, ChatRequest):
        #                                 args = {"request": req_value}
        #                             else:
        #                                 # Attempt pydantic validate
        #                                 args = {"request": ChatRequest.model_validate(req_value)}
        #                         else:
        #                             # Assume flat args correspond to ChatRequest fields
        #                             args = {"request": ChatRequest(**args)}
        #                     result = await tool.ainvoke(args)
        #                 except Exception as e:
        #                     result = f"Error executing tool '{name}': {e}"
        #             tool_msgs.append(ToolMessage(content=str(result), tool_call_id=call_id))

        #         final = llm_with_tools.invoke([*messages, ai_msg, *tool_msgs])
        #     else:
        #         final = ai_msg

        #     final_text = getattr(final, "content", final)
        #     # Optionally parse into structured output as a second pass
        #     if response_schema:
        #         llm_structured = llm.with_structured_output(response_schema)
        #         text_input = final_text if isinstance(final_text, str) else str(final_text)
        #         return llm_structured.invoke(text_input)
        #     return final_text
        # except Exception as e:
        #     return {"error": str(e)}