from graph.main_graph_tools import tools_dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, RemoveMessage, ToolMessage
from typing import TypedDict, Annotated


# Custom Reducer

def handle_messages_addition(state_messages: list[BaseMessage], messages_to_add: list[BaseMessage]):
    updated_state_messages = [state_message for state_message in state_messages]
    for message_to_add in messages_to_add:
        if isinstance(message_to_add, HumanMessage) or isinstance(message_to_add, AIMessage) or isinstance(message_to_add, ToolMessage):
            updated_state_messages.append(message_to_add)
        elif isinstance(message_to_add, RemoveMessage):
            index_of_message_to_remove_in_updated_state_messages = -1
            for index, update_state_message in enumerate(updated_state_messages):
                if update_state_message.id == message_to_add.id:
                    index_of_message_to_remove_in_updated_state_messages = index
                    break
            if index_of_message_to_remove_in_updated_state_messages >= 0:
                updated_state_messages.pop(index_of_message_to_remove_in_updated_state_messages)
    
    return updated_state_messages


class GeneralGraphState(TypedDict):
    general_messages: Annotated[list[BaseMessage], handle_messages_addition]
    tools_already_called: list
    general_summary: str
    ai_general_response: AIMessage


def execute_tools(state: GeneralGraphState) -> GeneralGraphState:
    general_messages = state.get('general_messages')
    last_general_message = general_messages[-1]
    tool_calls = last_general_message.tool_calls

    if (not isinstance(last_general_message, AIMessage)) or (not tool_calls):
        return
    tool_messages = []
    tools_already_called = []
    for tool_call in tool_calls:
        
        if tool_call['name'] in tools_dict:
            tools_already_called.append(tool_call)
            tool_name = tool_call['name']
            tool_id = tool_call['id']
            tool_args = tool_call['args']
            # print('CALLING TOOL WITH NAME = ', tool_name, 'AND ARGUMENTS ARE = ', tool_args)
            tool_response = tools_dict[tool_name].invoke(tool_args)
            tool_message = ToolMessage(content = str(tool_response), tool_call_id = tool_id)
            tool_messages.append(tool_message)
    # print('TOOL MESSAGES', tool_messages)
    return {'general_messages': tool_messages, 'tools_already_called': tools_already_called}


