from utils.graph_utils import handle_messages_addition, execute_tools

from pydantic import BaseModel, Field
from typing import TypedDict, Annotated

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, RemoveMessage
from graph.main_graph_tools import available_tools

from langgraph.graph import StateGraph, START, END

import files_to_load.config_to_load as config_to_load_at_initialization


class GeneralGraphState(TypedDict):
    general_messages: Annotated[list[BaseMessage], handle_messages_addition]
    tools_already_called: list
    general_summary: str
    ai_general_response: AIMessage

class GeneralGraphInputState(TypedDict):
    general_messages: Annotated[list[BaseMessage], handle_messages_addition]
    general_summary: str

class GeneralGraphOutputState(TypedDict):
    general_messages: Annotated[list[BaseMessage], handle_messages_addition]
    general_summary: str
    ai_general_response: AIMessage

def route_general_response(state: GeneralGraphState) -> GeneralGraphState:
    general_messages = state.get('general_messages')
    last_general_message = general_messages[-1]

    if isinstance(last_general_message, AIMessage):
        if not last_general_message.tool_calls:
            return 'generate_general_summary'
        else:
            return 'execute_tools'
    else:
        return '__end__'
    
class GeneralSummarySchema(BaseModel):
    general_summary: str = Field(description='summary of conversation between Human and AI.')
def generate_general_summary(state: GeneralGraphState) -> GeneralGraphState:
    general_summary_generation_llm = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(GeneralSummarySchema)

    general_messages = state.get('general_messages')
    conversation = []
    for general_message in general_messages:
        if isinstance(general_message, AIMessage):
            add_general_message = ('AI:', general_message.content)
        elif isinstance(general_message, HumanMessage):
            add_general_message = ('Human:', general_message.content)
        conversation.append(add_general_message)

    previous_general_summary = state.get('general_summary', '')
    if not previous_general_summary:
        prompt = f'''Task: Generate a concise, high-density summary of the following conversation.
                    Goal: The summary must capture all critical and necessary context an AI would need to accurately answer future user questions    without having to re-read the full transcript.
                    Constraints:
                    Be extremely precise and to the point.
                    Include all important decisions, unique facts, or specific user requirements discussed.
                    Conversation: {conversation}'''
        general_summary = general_summary_generation_llm.invoke(prompt).general_summary
        general_messages_to_delete = [RemoveMessage(id = general_message_to_delete.id) for general_message_to_delete in general_messages]
        ai_general_response = general_messages[-1]
        return {'general_summary': general_summary, 'general_messages': general_messages_to_delete, 'ai_general_response': AIMessage(content = ai_general_response.content)}

    prompt = f'''Synthesize and compress the following previous context summary and new conversation messages into a            single, updated summary.
            The final output must be token-efficient but comprehensive enough to provide complete, uninterrupted context for all future AI responses. Prioritize retaining all unique facts, user decisions, and action items, while eliminating redundancy.
            Previous Summary: "{previous_general_summary}"
            New Messages: {conversation}'''    
    general_summary = general_summary_generation_llm.invoke(prompt).general_summary
    general_messages_to_delete = [RemoveMessage(id = general_message_to_delete.id) for general_message_to_delete in general_messages]
    ai_general_response = general_messages[-1]
    # print('MESSAGES LIST TO DELETE = ', general_messages_to_delete)
    return {'general_summary': general_summary, 'general_messages': general_messages_to_delete, 'ai_general_response': AIMessage(content = ai_general_response.content)}


def generate_general_response(state: GeneralGraphState) -> GeneralGraphState:
    general_response_llm_with_tools = config_to_load_at_initialization.LLM_OPENAI.bind_tools(tools = available_tools)

    general_summary = state.get('general_summary', 'No Previous Conversation Summary Is Present')
    general_messages = state.get('general_messages')
    query = general_messages[0].content
    # print("SENDING QUERY = ", query)
    
    system_message = """
                    Objective: You are a helpful, responsible AI assistant. Your primary function is to accurately answer user queries by prioritizing your internal knowledge, leveraging external tools when necessary, and maintaining context from the conversation history.
                    Core Instruction Workflow:
                    Analyze Context: Identify the user's latest question. Use the past conversation history to fully understand the user's intent and resolve any ambiguity in the current query.
                    Prioritize Internal Knowledge: First, attempt to answer the question completely using only your own knowledge base.
                    Utilize Tools (If Necessary): If your internal knowledge is insufficient, determine if any equipped tools are relevant to finding the necessary information. Call the tool if it will provide a verifiable answer.
                    Formulate Final Response:
                    Do not hallucinate.
                    Provide the answer derived from your knowledge or tools.
                    If the question is unanswerable using both your knowledge and available tools, state clearly that you are unable to provide an answer.
                    """

    human_message = ''' 
                        Past Conversation Summary: "{general_summary}"
                        User's Question: {question}
                        '''

    prompt = ChatPromptTemplate(messages = [('system', system_message), ('human', human_message)]).invoke({
        'general_summary': general_summary,
        'question': query
    }).messages
    # print('PROMPT SENDING TO GENERATE RESPONSE = ', prompt)
    
    response = general_response_llm_with_tools.invoke(prompt)
    return {'general_messages': [response]}


def generate_general_response_using_tools_response(state: GeneralGraphState) -> GeneralGraphState:
    # print('HERE')
    general_response_llm_with_tools = config_to_load_at_initialization.LLM_OPENAI.bind_tools(tools = available_tools)

    general_summary = state.get('general_summary', 'No Previous Conversation Summary Is Present')
    general_messages = state.get('general_messages')
    tools_already_called = state.get('tools_already_called')
    query = general_messages[0]

    system_message = """
                    Objective: You are a **Final Answer Generator**. Your single and immediate task is to generate a comprehensive, human-readable response using the provided Tool Execution Results.

                    Core Instruction Workflow:

                    1. **FINAL SYNTHESIS (CRITICAL):** The 'Messages' list now contains a HumanMessage, an AIMessage requesting a tool, and a ToolMessage containing the raw results.
                    2. **PRIORITY:** You are **STRICTLY FORBIDDEN** from generating a new tool call. Your only valid output is a final, human-readable AIMessage that synthesizes the answer from the ToolMessage content.
                    3. **Hard Constraint:** If you find the required information (e.g., the weather) within the provided ToolMessage content, you **MUST** extract it and present it as the final answer.
                    4. **Tool Redundancy/Block:** Because you have just received tool results, if you generate a new tool call, you will violate the redundancy check and be terminated. Your only goal is to ANSWER the user now.
                    """
    
    human_message = """
                    Pase Conversation Summary: {general_summary}
                    User's Question: {question}
                    Tools Already Called: {list_of_tools_already_called}
                    Messages: {general_messages}
                    """
    # print('LIST OF TOOLS ALREADY CALLED = ', tools_already_called)
    # print('GENERAL MESSAGES = ', general_messages)
    prompt = ChatPromptTemplate(messages = [('system', system_message), ('human', human_message)]).invoke({
        'general_summary': general_summary,
        'question': query,
        'general_messages': general_messages,
        'list_of_tools_already_called': tools_already_called
    }).messages
    # print('THERE')
    response = general_response_llm_with_tools.invoke(prompt)
    # print('THEIR')
    return {'general_messages': [response]}


general_graph = StateGraph(state_schema=GeneralGraphState, input_schema=GeneralGraphInputState, output_schema=GeneralGraphOutputState)

general_graph.add_node('generate_general_summary', generate_general_summary)
general_graph.add_node('generate_general_response', generate_general_response)
general_graph.add_node('execute_tools', execute_tools)
general_graph.add_node('generate_general_response_using_tools_response', generate_general_response_using_tools_response)

general_graph.add_edge(START, 'generate_general_response')
general_graph.add_conditional_edges('generate_general_response', route_general_response, {'execute_tools': 'execute_tools', 'generate_general_summary': 'generate_general_summary', '__end__': END})
general_graph.add_edge('execute_tools', 'generate_general_response_using_tools_response')
general_graph.add_conditional_edges('generate_general_response_using_tools_response', route_general_response, {'execute_tools': 'execute_tools', 'generate_general_summary': 'generate_general_summary', '__end__': END})
general_graph.add_edge('generate_general_summary', END)
