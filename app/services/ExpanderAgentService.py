from langchain_google_genai import ChatGoogleGenerativeAI
from app.api.schemas.mcp_schema import ChatRequest

from app.core.logger import get_logger
from typing import Any

logging = get_logger(__name__)

agent = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=300,
    max_retries=2,
)
async def run_expander_agent(task: str) -> Any:
    logging.info("Running expander agent with task")
    system_prompt = (
        "You are a helpful AI assistant. Review the incoming list of tasks and determine if each can be handled by the tool: [create_notion_page].\n"
        " For the following tools this should be the response: \n"
        "- create_notion_page: this tool accepts a title, contents and type='notion' to create a Notion page. and the content is a very detailed infomration on what the notion page should have and the type must be notion for create_notion_page\n"
        "For tasks that can be handled, respond with a JSON array of objects, each strictly following this schema:\n"
        f"{ChatRequest.model_json_schema()}\n"
        "For tasks that cannot be handled, respond with a JSON object in this format:\n"
        '{ "answer": "payload.tasks", "type": "none" }\n'
        "Your response must be valid JSON and adhere strictly to the schema. Do not include any explanations or extra text.\n"
        "Examples:\n"
        "[{{'title': 'Minimal Notion Financial Spreadsheet', 'contents': 'In this page their should be a table that tracks the user financial data. and als their needs to be a component that allows users to input their expenses.', 'type': 'notion'}}]\n"
        '{ "answer": "talk to your friends", "type": "none" }'
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]
    logging.info(f"Expander Agent Message: {messages}")

    response = await agent.ainvoke(messages)
    output = getattr(response, "content", "")
    logging.info(f"Expander Agent Output: {output}, Task expander: {task}")
    return output
