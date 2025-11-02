from fastapi import APIRouter, Body, HTTPException
from typing import List
from app.core.logger import get_logger
from app.ai import input_schema as schema
from app.ai.ai import AI

logger = get_logger(__name__)


router = APIRouter()
@router.post("/")
async def ai(request: schema.AnyAgentRequest = Body(..., discriminator='agent_name')):
    """
    Routes request to the correct agent by `agent_name`, relies on Pydantic's
    discriminated union to validate `context`, invokes the AI agent, and validates
    the AI output against the corresponding response model before returning.
    """
    ai_instance = AI()

    agent_name = request.agent_name

    try:
        if agent_name == "clarifying":
            # request is ClarifyingAgentRequest due to discriminator validation
            result = ai_instance.clarify_agent(
                context=request.context,  # type: ignore[arg-type]
                user_prompt=request.user_prompt,
            )
            return result
            # Validate AI output against response model
            

        elif agent_name == "classifying":
            # Extract optional allowed_domains from generic context.data if provided
            allowed_domains: List[str] = ["tech", "health", "finance"]  # Default domains
            
            result = ai_instance.classify_agent(
                context=request.context,  # type: ignore[arg-type]
                allowed_domains=allowed_domains,
            )
            return result

        elif agent_name == "domain":
            result = ai_instance.domain_agent(
                context=request.context,  # type: ignore[arg-type]
            )
            return result

        elif agent_name == "tasks":
            result = ai_instance.task_agent(
                context=request.context,  # type: ignore[arg-type]
            )
            return result

        else:
            raise HTTPException(status_code=400, detail="Invalid agent name.")

    except ValueError as e:
        # Likely JSON parsing issues from AI output
        raise HTTPException(status_code=400, detail=f"AI output parsing error: {str(e)}")
    except Exception as e:
        # Generic safety net
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
