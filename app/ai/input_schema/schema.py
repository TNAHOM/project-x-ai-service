from pydantic import BaseModel, Field
import json
from typing import Any, Dict, List, Optional, Union, Literal

class ProblemSpaceModel(BaseModel):
    name: str
    description: str
    status: str = 'active'

class DomainProfileModel(BaseModel):
    domain_type: str
    personality: str

class TaskModel(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = 'pending'
    is_automated: bool = True

# --- Base Models for Context (Simplified) ---
class ClarifyingContext(BaseModel):
    history: List[Dict[str, str]]
    data: Optional[Dict[str, Any]] = None

class ClassifyingContext(ClarifyingContext):
    pass

class DomainContext(ClarifyingContext):
    domain_profile: DomainProfileModel # Use the new structured model
    problem_space: ProblemSpaceModel
    knowledge_base_summary: Optional[Dict[str, Any]] = None

class TaskContext(DomainContext):
    strategies: List[str]

# --- Request Models (Updated to use new models) ---
class AgentRequest(BaseModel):
    agent_name: str
    user_prompt: str

class ClarifyingAgentRequest(AgentRequest):
    agent_name: Literal["clarifying"]
    context: ClarifyingContext

class ClassifyingAgentRequest(AgentRequest):
    agent_name: Literal["classifying"]
    context: ClassifyingContext

class DomainAgentRequest(AgentRequest):
    agent_name: Literal["domain"]
    context: DomainContext

class TasksAgentRequest(AgentRequest):
    agent_name: Literal["tasks"]
    context: TaskContext

AnyAgentRequest = Union[
    ClarifyingAgentRequest, ClassifyingAgentRequest, DomainAgentRequest, TasksAgentRequest
]

# --- MODIFIED: Response Models ---
class ClarifyingAgentResponse(BaseModel):
    clarifying_questions: List[str]
    premade_answers: List[str]

class ClassifyingAgentResponse(BaseModel):
    # This agent now returns structured objects
    problem_space: ProblemSpaceModel
    domain_profile: DomainProfileModel

class DomainAgentResponse(BaseModel):
    solutions: List[str] 

class TasksAgentResponse(BaseModel):
    # This agent now returns a list of Task objects
    tasks: List[TaskModel]
