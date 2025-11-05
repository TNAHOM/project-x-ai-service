from fastapi import APIRouter
from app.services.ExecutionAgentService import ExecutionAgentService
from app.core.logger import get_logger
from app.api.schemas.agent_schema import AgentMessage

import json
from langchain_google_genai import ChatGoogleGenerativeAI

from app.services.ExpanderAgentService import run_expander_agent

llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                max_tokens=None,
                timeout=300,
            )

router = APIRouter()
agent_service = ExecutionAgentService()
logger = get_logger(__name__)


# @router.post("/run-agent/")
# async def excutable_main_agent(payload: AgentMessage):
#     logger.info("Received tasks for agent")

#     tasks = payload.tasks
#     systemPrompt = """
#     You are a helpful AI assistant. That checks the incoming list of tasks. and deside if they are automatable or not based on the tool you have been provided with. And respond strictly in the given response_schema.
#     """
    
#     message = agent_service.message(incomingData=tasks, systemPrompt=systemPrompt)

#     response = await agent_service.run_agent(message, response_schema=ExecutorAgentResponseSchema.model_json_schema())

#     logger.info(f"Agent response: {response}")
#     return {"response": response}

@router.post("/expander-agent/")
async def expander_agent(payload: AgentMessage):
    logger.info("Received tasks for expander agent")
    try:
        tasks = payload.tasks
        output = []
        for task in tasks:
            logger.info(f"Task: {task}")
            # Pass all tasks at once
            response = await run_expander_agent(str(task))
            # Remove code block markers if present
            if response.strip().startswith("```"):
                response = response.strip().lstrip("`json").strip("`").strip()
                # Remove any leading/trailing code block markers
                if response.startswith("json"):
                    response = response[4:].strip()
            # Parse response (assuming it's JSON)
            parsed = json.loads(response)
            # If the response is a list, wrap it in the expected schema
            if isinstance(parsed, list):
                output.extend(parsed)
            # If the response is an object with "answer", handle accordingly
            elif isinstance(parsed, dict) and "answer" in parsed:
                output.append({"title": task, "contents": parsed["answer"], "type": "none"})
            else:
                output.append({"title": task, "contents": "Unable to process task.", "type": "none"})
        
        executionOutput = []
        for outputtasks in output:
            # check if the key type is none
            print("check the type", outputtasks.get("type"))
            if outputtasks.get("type") == "none":
                executionOutput.append(outputtasks)
                continue
            executionAgent = await agent_service.run_agent(messageRequest=outputtasks)
            executionOutput.append(executionAgent)

        return {"executionOutput": executionOutput}
    except Exception as e:
        logger.error(f"Error in expander agent: {str(e)}")
        return {"error": str(e)}