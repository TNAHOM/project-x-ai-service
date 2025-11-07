from venv import logger
from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
import json
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.globals import set_debug
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_perplexity import ChatPerplexity
from app.ai import output_schema, input_schema, prompt
from dotenv import load_dotenv
from app.services.ExecutionAgentService import ExecutionAgentService
from app.api.schemas.mcp_schema import ChatRequest

load_dotenv()
set_debug(True)

class AI():
    def __init__(self):
        # self.model = init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0.1, top_p = 0.5)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        self.perplexity_llm = ChatPerplexity(temperature=0, model="sonar", timeout=1800)

    def parse_json_like_content(self, input_text):
        """
        Parse a JSON-like string that may contain code block markers or a `json` prefix.
        """
        # If input_text is an AIMessage, get the content string
        if hasattr(input_text, "content"):
            input_text = input_text.content

        # Step 1: Remove code block markers if present
        if input_text.startswith("```"):
            input_text = input_text[3:].strip()

        if input_text.endswith("```"):
            input_text = input_text[:-3].strip()

        # Step 2: Remove the `json` prefix if present
        if input_text.startswith("json"):
            input_text = input_text[4:].strip()

        # Step 3: Parse the JSON content
        try:
            return json.loads(input_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")



# {user_prompt} (user's problem description)
# {history} (list of conversation turns)
    def clarify_agent(self, context: input_schema.ClarifyingContext, user_prompt: str|None ):
        logger.info("Clarify Agent Invoked with context:", extra={"context": context.model_dump()})
        try:
            clarify_prompt = ChatPromptTemplate.from_messages([
                # SystemMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt),
                HumanMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt)
            ])

            clarifyingAgent = self.llm.with_structured_output(output_schema.ClarifyingAgentOutput)
        
            result_text = (clarify_prompt | clarifyingAgent).invoke({
                "history": context.history,
                "user_prompt": user_prompt
            })

        except Exception as e:
            logger.error("Clarify Agent failed", exc_info=e)
            raise
        # print("Clarify Agent Result:", result_text)

        return result_text


# {history} (list of conversation turns)
# {allowed_domains} (list of strings)
    def classify_agent(self, context: input_schema.ClassifyingContext):

        logger.info("Classify Agent Invoked with context:", extra={"context": context.model_dump()})
        try:
            classify_prompt = ChatPromptTemplate.from_messages([
                # SystemMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt),
                HumanMessagePromptTemplate.from_template(prompt.ClassifyingAgentPrompt)
            ])
        
            classifyingAgent = self.llm.with_structured_output(output_schema.ClassifyingAgentOutput)
        

            result_text = (classify_prompt | classifyingAgent).invoke({
                "history": context.history,
                "allowed_domains": input_schema.AllowedDomains
            })
        except Exception as e:
            logger.error("Classify Agent failed", exc_info=e)
            raise

        return result_text

# *   {problem_space} (json object)
# *   {domain_profile} (json object)
# *   {knowledge_base_summary} (json object)
    def domain_agent(self, context: input_schema.DomainContext, user_prompt: str|None):
        input_prompt = ""
        if context.domain_profile.domain_type == "finance":
            input_prompt = prompt.FinanceDomainAgentPrompt
        elif context.domain_profile.domain_type == "personal":
            input_prompt = prompt.PersonalDomainAgentPrompt
        elif context.domain_profile.domain_type == "professional":
            input_prompt = prompt.ProfessionalDomainAgentPrompt
        
        try:
            domain_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(input_prompt),
            ])

            domainAgent = self.llm.with_structured_output(output_schema.DomainAgentOutput)
            result_text = (domain_prompt | domainAgent).invoke({
                "problem_space": json.dumps(context.problem_space.model_dump()),
                "previous_strategies":  [strategies.model_dump() for strategies in context.previous_objectives] if context.previous_objectives else None,
                "user_prompt": user_prompt,
                "domain_profile": json.dumps(context.domain_profile.model_dump()),
                "knowledge_base_summary": json.dumps(context.knowledge_base_summary)
            })
        except Exception as e:
            logger.error("Domain Agent failed", exc_info=e)
            raise

        return result_text


#  {problem_space} (json object)
# *   {domain_profile} (json object)
# *   {knowledge_base_summary} (json object)
# *   {strategic_objective} (
    def task_agent(self, context: input_schema.TaskContext, user_prompt: str|None):
        try:
            task_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(prompt.TasksAgentPrompt),
            ])

            taskAgent = self.perplexity_llm.with_structured_output(output_schema.TasksAgentOutput)
            
            result_text = (task_prompt | taskAgent).invoke({
                "problem_space": json.dumps(context.problem_space.model_dump()),
                "domain_profile": json.dumps(context.domain_profile.model_dump()),
                "strategic_objective": [strategies.model_dump() for strategies in context.strategies],
                "previous_tasks": [tasks.model_dump() for tasks in context.previous_tasks] if context.previous_tasks else None,
                "user_prompt": user_prompt,
                "knowledge_base_summary": json.dumps(context.knowledge_base_summary),
            })
        except Exception as e:
            logger.error("Task Agent failed", exc_info=e)
            raise

        return result_text
    
    def automation_agent(self, context: input_schema.AutomationContext, user_prompt: str|None):
        logger.info("Automation Agent Invoked with context:", extra={"context": context})
        try:
            automation_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(prompt.AutomationAgentPrompt)
            ])

            automationAgent = self.llm.with_structured_output(output_schema.AutomationAgentOutput)
        
            result_text = (automation_prompt | automationAgent).invoke({
                "available_tools": json.dumps(prompt.AvailableTools),
                "tasks": json.dumps([task.model_dump() for task in context.tasks]),
                "knowledge_base": json.dumps(context.knowledge_base),
                "history": json.dumps(context.history),
                "data": json.dumps(context.data) if context.data else None,
                "user_prompt": user_prompt,


            })

        except Exception as e:
            logger.error("Automation Agent failed", exc_info=e)
            raise

        return result_text
    
    async def execution_agent(self, context: input_schema.ExecutionContext, user_prompt: str|None):
        agent_service = ExecutionAgentService()
        response = await agent_service.run_agent(context, user_prompt)
        return response

    
    def knowledge_base_agent(self, context: input_schema.KnowledgeBaseContext, user_prompt: str|None):
        logger.info("Knowledge Base Agent Invoked with context:", extra={"context": context})
        try:
            kb_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(prompt.KnowledgeBaseAgentPrompt)
            ])

            knowledgeBaseAgent = self.llm.with_structured_output(output_schema.KnowledgeBaseAgentOutput)
        
            result_text = (kb_prompt | knowledgeBaseAgent).invoke({
                "knowledge_base": json.dumps(context.knowledge_base)
                ,"user_prompt": user_prompt
            })

        except Exception as e:
            logger.error("Knowledge Base Agent failed", exc_info=e)
            raise

        return result_text
    
    def venting_agent(self, context: input_schema.VentingContext, user_prompt: str|None):
        logger.info("Venting Agent Invoked with context:", extra={"context": context})
        try:
            venting_prompt = ChatPromptTemplate.from_messages([
                HumanMessagePromptTemplate.from_template(prompt.VentingAgentPrompt)
            ])

            ventingAgent = self.llm.with_structured_output(output_schema.VentingAgentOutput)
        
            result_text = (venting_prompt | ventingAgent).invoke({
                "user_memory": json.dumps(context.user_memory),
                "user_prompt": user_prompt,
                "history": json.dumps(context.history)


            })

        except Exception as e:
            logger.error("Venting Agent failed", exc_info=e)
            raise

        return result_text

        

   


