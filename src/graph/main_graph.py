from utils.graph_utils import handle_messages_addition
from graph.rag_graph import rag_graph
from graph.general_graph import general_graph

from typing import TypedDict, Annotated, Literal, Optional
from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage




# Main Graph

class MainGraphState(TypedDict, total=False):
    call_which_subgraph: Literal['rag', 'general']
    question: str
    response: AIMessage
    human_feedback: str
    all_messages: Annotated[list[BaseMessage], handle_messages_addition]

    general_messages: Optional[Annotated[list[BaseMessage], handle_messages_addition]]
    general_summary: Optional[str]
    ai_general_response: Optional[AIMessage]

    rag_messages: Optional[Annotated[list[BaseMessage], handle_messages_addition]]
    rag_summary: Optional[str]
    ai_rag_response: Optional[AIMessage]
    small_document_ids: Optional[list[str]] = []
    large_document_ids: Optional[list[str]] = []
    files_large_documents_ids: Optional[dict]
    files_small_documents_ids: Optional[dict]
    files_data: Optional[str]
    files_data_dict: Optional[dict]
    answer_provided: Optional[bool]


def add_question_to_relevant_subgraph_messages(state: MainGraphState) -> MainGraphState:
    question = state.get('question')
    call_sub_graph = state.get('call_which_subgraph')
     
    if call_sub_graph == 'rag':
        return {'rag_messages': [HumanMessage(content=question, id=str(uuid4()))], 'all_messages': [HumanMessage(content = question)]}
    else:
        return {'general_messages': [HumanMessage(content=question, id=str(uuid4()))], 'all_messages': [HumanMessage(content = question)]}

def route_between_rag_and_general_subgraphs(state: MainGraphState) -> str:
    call_sub_graph = state.get('call_which_subgraph')
    
    if call_sub_graph == 'rag':
        # print('CALLING RAG SUBGRAPH = ', call_sub_graph)
        return 'call_rag_subgraph'
    else:
        # print('CALLING GENERAL SUBGRAPH = ', call_sub_graph)
        return 'call_general_subgraph'

def receive_general_subgraph_response(state: MainGraphState) -> MainGraphState:
    response = state.get('ai_general_response')
    return {'response': AIMessage(content = response.content), 'all_messages': [AIMessage(content = response.content)]}

def analyzed_rag_subgraph_response_and_decide_about_human_feedback(state: MainGraphState) -> MainGraphState:
    
    answer_provided = state.get('answer_provided')
    if answer_provided:
        response = state.get('ai_rag_response')
        return {'response': AIMessage(content = response.content), 'all_messages': [AIMessage(content = response.content)]}
    else:
        human_feedback = interrupt(value = 'RAG is unable to provide answer. Would you like to get answer without using RAG ? Reply Only With yes or no.')
        # print('HUMAN FEEDBACK RECEIVED = ', human_feedback, 'PREVIOUS CALLED SUBGRAPH WAS = ', state.get('call_which_subgraph'))

        if human_feedback == 'no':
            # print('FEEDBACK IS = ', human_feedback)
            return {'human_feedback': 'no', 'all_messages': [AIMessage(content = 'Sorry, Unable to answer your question from provided files')], 'response': AIMessage(content = 'Sorry, Unable to answer your question from provided files')}
        else:
            # print('FEEDBACK IS = ', human_feedback)
            return {'human_feedback': 'yes', 'call_which_subgraph': 'general'}
    
    
def route_based_on_human_feedback(state: MainGraphState) -> MainGraphState:
    call_which_subgraph = state.get('call_which_subgraph')
    if call_which_subgraph == 'rag':
        answer_provided = state.get('answer_provided')
        if answer_provided:
            return '__end__'
    human_feedback = state.get('human_feedback')
    if not human_feedback:
        return '__end__'
    elif human_feedback == 'no':
        return '__end__'
    elif human_feedback == 'yes':
        return 'add_question_to_relevant_subgraph_messages'
    

class OutputMainGraphState(TypedDict):
    question: str
    response: AIMessage
    human_feedback: str

    general_summary: Optional[str]
    ai_general_response: Optional[AIMessage]

    rag_summary: Optional[str]
    answer_provided: Optional[bool]
    ai_rag_response: AIMessage



main_graph = StateGraph(state_schema=MainGraphState, output_schema=OutputMainGraphState)

main_graph.add_node('add_question_to_relevant_subgraph_messages', add_question_to_relevant_subgraph_messages)
main_graph.add_node('rag_subgraph',rag_graph.compile())
main_graph.add_node('general_subgraph', general_graph.compile())
main_graph.add_node('receive_general_subgraph_response', receive_general_subgraph_response)
main_graph.add_node('analyzed_rag_subgraph_response_and_decide_about_human_feedback', analyzed_rag_subgraph_response_and_decide_about_human_feedback)

main_graph.add_edge(START, 'add_question_to_relevant_subgraph_messages')

main_graph.add_conditional_edges('add_question_to_relevant_subgraph_messages', route_between_rag_and_general_subgraphs, 
{'call_rag_subgraph': 'rag_subgraph', 'call_general_subgraph': 'general_subgraph'})

main_graph.add_edge('general_subgraph', 'receive_general_subgraph_response')
main_graph.add_edge('receive_general_subgraph_response', END)

main_graph.add_edge('rag_subgraph', 'analyzed_rag_subgraph_response_and_decide_about_human_feedback')
main_graph.add_conditional_edges('analyzed_rag_subgraph_response_and_decide_about_human_feedback', route_based_on_human_feedback, {'__end__': END, 'add_question_to_relevant_subgraph_messages': 'add_question_to_relevant_subgraph_messages'})






