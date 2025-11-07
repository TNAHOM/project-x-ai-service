from pydantic import BaseModel, Field
import json
from typing import Any, Dict, List, Optional, Union, Literal
from regex import T
from sqlalchemy import Enum
from pydantic import BaseModel, Field, field_validator 

AllowedDomains = ["finance", "personal", "professional"]
    

class ProblemSpaceModel(BaseModel):
    name: str
    description: str
    status: str = 'active'

class DomainProfileModel(BaseModel):
    domain_type: str
    personality: str

class TaskModel(BaseModel):
    order: int
    name: str
    description: Optional[str] = None
    status: str = 'pending'
    is_automated: bool = True

class StrategyModel(BaseModel):
    strategy_name: str
    approach_summary: str
    key_objectives: List[str]

# --- Base Models for Context (Simplified) ---
class BaseContext(BaseModel):
    history: List[Dict[str, str]]
    data: Optional[Dict[str, Any]] = None

class ClarifyingContext(BaseContext):
    pass

class ClassifyingContext(BaseContext):
    pass

class DomainContext(ClarifyingContext):
    problem_space: ProblemSpaceModel
    domain_profile: DomainProfileModel # Use the new structured model
    knowledge_base_summary: Optional[Dict[str, Any]] = None
    previous_objectives: Optional[List[TaskModel]] = None

class TaskContext(DomainContext):
    strategies: List[StrategyModel]
    previous_tasks: Optional[List[TaskModel]] = None

class AutomationContext(BaseContext):
    tasks: List[TaskModel]
    knowledge_base: Dict[str, Any]

# --- Meta Agents context ---#
class KnowledgeBaseContext(BaseModel):
    knowledge_base: Dict[str, Any]

class VentingContext(BaseModel):
    user_memory: List[Dict[str, Any]]
    history: List[str]

class ExecutionContext(BaseModel):
    """
        Schema For Incoming Chat Requests from the Frontend 
        That contains title, contents and type of tool to be used.
    """
    title: Optional[str] = None
    contents: Optional[str] = None
    type: Optional[str] = None
    # --- Add Notion Mode ----
    

# --- Request Models (Updated to use new models) ---
class AgentRequest(BaseModel):
    agent_name: str
    user_prompt: Optional[str] = None

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

class AutomationAgentRequest(AgentRequest):
    agent_name: Literal["automation"]
    context: AutomationContext

# --- Meta agent context --- #
class KnowledgeBaseAgentRequest(AgentRequest):
    agent_name: Literal["knowledge_base"]
    context: KnowledgeBaseContext

class VentingAgentRequest(AgentRequest):
    agent_name: Literal["venting"]
    context: VentingContext

class ExecutionAgentRequest(AgentRequest):
    agent_name: Literal["execution"]
    context: Optional[ExecutionContext]
    
AnyAgentRequest = Union[
    ClarifyingAgentRequest, ClassifyingAgentRequest, DomainAgentRequest, TasksAgentRequest, KnowledgeBaseAgentRequest, VentingAgentRequest, AutomationAgentRequest, ExecutionAgentRequest
]

