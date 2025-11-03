"""Output schemas for AI agents based on their prompts.

These Pydantic models mirror the exact JSON shapes each agent is instructed
to return in its prompt templates under `app.prompt`:

- ClarifyingAgentPrompt -> ClarifyingAgentOutput
- ClassifyingAgentPrompt -> ClassifyingAgentOutput (+ nested ProblemSpaceOutput)
- FinanceDomainAgentPrompt -> DomainAgentOutput
- TasksAgentPrompt -> TasksAgentOutput (+ nested TaskItemOutput)

Note: These are output-only shapes to validate/model the AI responses. They are
kept separate from request/context models in `app.schema`.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# --- Clarifying Agent ---
class ClarifyingAgentOutput(BaseModel):
	"""Output for the Clarifying agent as specified in ClarifyingAgentPrompt.

	Example shape (when not yet clear):
	{
	  "is_problem_clear": false,
	  "clarifying_question": "...",
	  "suggested_answers": ["...", "...", "...", "...", "Other/None of the above."]
	}

	When clear:
	{
	  "is_problem_clear": true,
	  "clarifying_question": null,
	  "suggested_answers": []
	}
	"""

	is_problem_clear: bool = Field(..., description="Whether the problem is sufficiently understood.")
	clarifying_question: Optional[str] = Field(
		None,
		description="Next best clarifying question to ask, null if the problem is clear.",
	)
	suggested_answers: List[str] = Field(
		default_factory=list,
		description="Suggested answer options for the clarifying question.",
		min_length=0,
	)


# --- Classifying Agent ---
class ProblemSpaceOutput(BaseModel):
	"""Structured problem space as required by ClassifyingAgentPrompt.

	Includes a concise name, a descriptive paragraph, and a single-sentence root cause.
	"""

	name: str = Field(..., description="3-5 word concise title of the problem.")
	description: str = Field(
		..., description="Detailed one-paragraph summary (goal, action, expected vs actual)."
	)
	root_cause: str = Field(
		..., description="Specific one-sentence statement of the core reason for the issue."
	)


class ClassifyingAgentOutput(BaseModel):
	"""Output for the Classifying agent as specified in ClassifyingAgentPrompt."""

	domain: str = Field(
		..., description="The selected domain (must be one of the allowed domains provided to the agent)."
	)
	justification: str = Field(
		..., description="A brief one-sentence justification for the selected domain."
	)
	problem_space: ProblemSpaceOutput = Field(
		..., description="Structured problem definition for downstream specialist agents."
	)


# --- Domain Agent ---
class DomainStrategyOutput(BaseModel):
    """Single strategy option produced by the Domain agent."""

    strategy_name: str = Field(
        ..., description="Compelling strategy name that reflects the goal and user personality."
    )
    approach_summary: str = Field(
        ..., description="Concise 1-2 sentence summary of the strategy's core philosophy."
    )
    key_objectives: List[str] = Field(
        ..., min_length=7, max_length=10, description="List of 7-10 high-level strategic objectives."
    )


class DomainAgentOutput(BaseModel):
    """Output for the Domain agent as specified in FinanceDomainAgentPrompt.

    Produces a list of high-level strategies aligned with the user's personality.
    """

    strategies: List[DomainStrategyOutput] = Field(
        ...,
        min_length=1,
        description="Ordered list of strategy options tailored to the user's personality and goal.",
    )


# --- Tasks Agent ---
class TaskItemOutput(BaseModel):
	"""Single execution task item as required by TasksAgentPrompt."""
	order: int = Field(..., description="Execution order of this task in the overall plan.")
	name: str = Field(..., description="Short task name.")
	description: str = Field(..., description="Concrete, actionable task description.")
	is_automated: bool = Field(
		..., description="Whether this task can be automated by the agent/system."
	)


class TasksAgentOutput(BaseModel):
	"""Output for the Tasks agent as specified in TasksAgentPrompt."""

	overall_status: Literal["completed", "failed"] = Field(
		..., description='Overall outcome of the end-to-end plan ("completed" or "failed").'
	)
	research_summary: str = Field(
		..., description="Summary of research that informed the execution plan."
	)
	task: List[TaskItemOutput] = Field(
		..., description="Granular, step-by-step execution plan items."
	)


__all__ = [
	"ClarifyingAgentOutput",
	"ProblemSpaceOutput",
	"ClassifyingAgentOutput",
	"DomainAgentOutput",
	"TaskItemOutput",
	"TasksAgentOutput",
]

