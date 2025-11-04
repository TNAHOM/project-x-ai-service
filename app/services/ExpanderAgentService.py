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
        "You are a helpful AI assistant. Review the incoming tasks and determine if each can be handled by the available tools: [create_notion_page, create_google_doc].\n"
        "Tools and expected types: \n"
        "- create_notion_page: accepts title, contents, type='notion' to create/update a Notion page. Contents should describe what the page should include.\n"
        "- create_google_doc: accepts title, contents, type in {'google-docs','google-sheets'} to create/update a Google Doc or a Google Sheet. For sheets, contents can describe a table to insert.\n"
        "For tasks that can be handled, respond with a JSON array of objects, each strictly following this schema:\n"
        f"{ChatRequest.model_json_schema()}\n"
        "For tasks that cannot be handled, respond with a JSON object in this format:\n"
        '{ "answer": "payload.tasks", "type": "none" }\n'
        "Your response must be valid JSON and adhere strictly to the schema. Do not include any explanations or extra text.\n"
        "Examples:\n"
        "[{{'title': 'Project Plan', 'contents': 'Create a detailed project plan with milestones and tasks.', 'type': 'google-docs'}},\n"
        " {'title': 'Monthly Budget', 'contents': 'Create a sheet with columns: Category, Amount, Date. Add example rows for Rent 1200 and Utilities 200.', 'type': 'google-sheets'}]\n"
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
