from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
import json
from typing import Any, Dict, List, Optional, Union, Literal
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import init_chat_model
from langchain_core.globals import set_debug
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.ai import output_schema, input_schema, prompt
from dotenv import load_dotenv
load_dotenv()
set_debug(True)

class AI():
    def __init__(self):
        # self.model = init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0.1, top_p = 0.5)
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

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
    def clarify_agent(self, context: input_schema.ClarifyingContext, user_prompt: str):

        clarify_prompt = ChatPromptTemplate.from_messages([
            # SystemMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt),
            HumanMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt)
        ])

        clarifyingAgent = self.llm.with_structured_output(output_schema.ClarifyingAgentOutput)
        result_text = (clarify_prompt | clarifyingAgent).invoke({
            "history": context.history,
            "user_prompt": user_prompt
        })

        print("Clarify Agent Result:", result_text)

        return result_text


# {history} (list of conversation turns)
# {allowed_domains} (list of strings)
    def classify_agent(self, context: input_schema.ClassifyingContext, allowed_domains: List[str]):

        classify_prompt = ChatPromptTemplate.from_messages([
            # SystemMessagePromptTemplate.from_template(prompt.ClarifyingAgentPrompt),
            HumanMessagePromptTemplate.from_template(prompt.ClassifyingAgentPrompt)
        ])

        classifyingAgent = self.llm.with_structured_output(output_schema.ClassifyingAgentOutput)
        result_text = (classify_prompt | classifyingAgent).invoke({
            "history": context.history,
            "allowed_domains": json.dumps(allowed_domains)
        })

        return result_text

# *   {problem_space} (json object)
# *   {domain_profile} (json object)
# *   {knowledge_base_summary} (json object)
    def domain_agent(self, context: input_schema.DomainContext):
        

        domain_prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(prompt.DomainAgentPrompt),
        ])

        domainAgent = self.llm.with_structured_output(output_schema.DomainAgentOutput)
        result_text = (domain_prompt | domainAgent).invoke({
            "problem_space": json.dumps(context.problem_space.model_dump()),
            "domain_profile": json.dumps(context.domain_profile.model_dump()),
            "knowledge_base_summary": json.dumps(context.knowledge_base_summary)
        })

        return result_text


#  {problem_space} (json object)
# *   {domain_profile} (json object)
# *   {knowledge_base_summary} (json object)
# *   {strategic_objective} (
    def task_agent(self, context: input_schema.TaskContext):
        task_prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(prompt.TasksAgentPrompt),
        ])

        taskAgent = self.llm.with_structured_output(output_schema.TasksAgentOutput)
        result_text = (task_prompt | taskAgent).invoke({
            "problem_space": json.dumps(context.problem_space.model_dump()),
            "domain_profile": json.dumps(context.domain_profile.model_dump()),
            "knowledge_base_summary": json.dumps(context.knowledge_base_summary),
            "strategic_objective": json.dumps(context.strategies)
        })

        return result_text

        

   


