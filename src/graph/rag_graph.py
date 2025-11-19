from pydantic import BaseModel, Field
from typing import TypedDict, List, Annotated, Optional
from uuid import uuid4
import math

from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, RemoveMessage

from langgraph.graph import StateGraph, START, END
from langchain.retrievers import MergerRetriever, ContextualCompressionRetriever
from langchain.document_transformers import EmbeddingsRedundantFilter, LongContextReorder
from langchain.retrievers.document_compressors import DocumentCompressorPipeline

from utils.graph_utils import handle_messages_addition

import files_to_load.config_to_load as config_to_load_at_initialization


# RAG Implementation

# Define RAG Graph State

class RAGGraphState(TypedDict):
    small_document_ids: Optional[list[str]] = []
    large_document_ids: Optional[list[str]] = []
    rag_messages: Annotated[list[BaseMessage], handle_messages_addition]
    files_data: str
    files_data_dict: dict
    files_large_documents_ids: Optional[dict]
    files_small_documents_ids: Optional[dict]
    all_docs_needed: bool
    docs_needed_of_files: List[str]
    all_files_sorted_docs: dict
    rag_summary: str
    queries: list[str]
    retrieved_documents: list[str]
    unique_retrieved_documents: list[str]
    formatted_docs: str
    answer_provided: bool
    ai_rag_response: AIMessage

class RAGGraphInputState(TypedDict):
    small_document_ids: Optional[list[str]] = []
    large_document_ids: Optional[list[str]] = []
    rag_messages: Annotated[list[BaseMessage], handle_messages_addition]
    rag_summary: str
    files_data: str
    files_data_dict: dict
    files_large_documents_ids: Optional[dict]
    files_small_documents_ids: Optional[dict]

class RAGGraphOutputState(TypedDict):
    small_document_ids: Optional[list[str]] = []
    large_document_ids: Optional[list[str]] = []
    rag_messages: Annotated[list[BaseMessage], handle_messages_addition]
    rag_summary: str
    files_data: str
    files_data_dict: dict
    files_large_documents_ids: Optional[dict]
    files_small_documents_ids: Optional[dict]
    answer_provided: bool
    ai_rag_response: AIMessage




# Define RAG Graph Nodes

def generate_queries(state: RAGGraphState) -> RAGGraphState:
    queires_generation_llm = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(QueriesGenerationSchema)
    
    rag_messages = state.get('rag_messages')
    conversation = []
    for rag_message in rag_messages:
        if isinstance(rag_message, AIMessage):
            add_rag_message = ('AI', rag_message.content)
        elif isinstance(rag_message, HumanMessage):
            add_rag_message = ('Human', rag_message.content)
        conversation.append(add_rag_message)

    prompt = ChatPromptTemplate(messages = [('human', 'You have genenrate 3 queries similar to original query considering the original query and past conversation summary and current conversation messages if provided which are given below. Use past conversation and current conversation only if original query is ambigous and not clear to formula new queries. \n original query: "{original_query}." \n previous conversation summary: "{rag_summary}" \n current conversation messages: {conversation} \n Generate 3 queries in such way that when send to RAG document retrieval will retrive most relevant documents to answer the original query')]).invoke({
        'original_query': state.get('rag_messages')[-1].content,
        'rag_summary': state.get('rag_summary', 'Previous Conversation Not Available'),
        'conversation': conversation
    })
    response = queires_generation_llm.invoke(prompt)
    queries = response.queries
    # print('ORIGINAL QUERY SEND = ', state.get('rag_messages')[-1].content)
    # print('RESPONSE OF QUERIES GENERATION = ', response)
    # print('QUERIES GENERATED = ', queries)
    return {'queries': queries}

class CategorizeQuestionSchema(BaseModel):
    need_all_docs: bool = Field(..., description='True, if all docs required of specific or all files to answer user question')
    docs_needed_of_files: Optional[List[str]] = Field(description='list of files names whose all docs are required to answer user question')
def categorize_question(state: RAGGraphState) -> RAGGraphState:
    questions = state.get('queries')
    system_message = """
                    You are an expert RAG Routing and Categorization Agent.

                    **Primary Task:** Determine if the user's questions require a synthesis of the ENTIRE **BODY CONTENT** of a specific file or files.

                    **Decision Rules for 'need_all_docs':**
                    1. **Set 'need_all_docs' to TRUE only if:**
                        * The user requires a **SYNTHESIS** or **COMPREHENSIVE ANALYSIS** of the entire document's **BODY TEXT** (e.g., Summary, Main Findings, Full Report, Structural Overview).
                        * Setting TRUE indicates the answer cannot be generated without processing complete file.

                    2. **Set 'need_all_docs' to FALSE if (HIGH PRIORITY):**
                        * The question asks for any **SINGLE, EXTRACTABLE FACT** or **METADATA**.
                        * This includes the **Author(s), Title, Publication Date, single definition, single number, or a quote**.
                        * **MANDATORY EXCLUSION:** If the question can be answered *solely* by looking at the file's metadata (Author, Title, Topic) or by retrieving a tiny, specific text span, you **MUST** set 'need_all_docs' to **FALSE**.

                    ---

                    **FILENAME EXTRACTION (MANDATORY):**
                    If 'need_all_docs' is TRUE, you MUST identify the exact file name(s) from the 'Files Available' list.
                    [... include your ABSOLUTE STRING COPY RULE here, as it's now working ...]
                    """
    human_message = '''

                    User Questions: {questions}
                    Files Available: {files_data}

                    '''
    files_data = state.get('files_data')
    # print('FILES DATA SENDING TO CATEGORIZE = ', files_data)

    prompt = ChatPromptTemplate(messages=[('system', system_message), ('human', human_message)]).invoke({
        'questions': questions,
        'files_data': files_data
    })

    response = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(CategorizeQuestionSchema).invoke(prompt)
    # print('CATEGORIZE RAG QUESTION RESULT: ', response)
    return {'all_docs_needed': response.need_all_docs, 'docs_needed_of_files': response.docs_needed_of_files}

def route_rag_question(state: RAGGraphState) -> str:
    all_docs_needed = state.get('all_docs_needed')
    if all_docs_needed:
        return 'all_docs_rag_response_route'
    return 'rag_response_route'

def fetch_doc_index(document):
    return document.metadata.get('order_id')

def retrieve_all_docs(state: RAGGraphState) -> RAGGraphState:
    # print('RETRIEVING ALL DOCS')
    docs_needed_of_files = state.get('docs_needed_of_files')
    files_sorted_docs = {}
    for doc_needed_of_file in docs_needed_of_files:
        # print('RETRIEVING ALL DOCS OF FILE', doc_needed_of_file)
        
        large_documents_ids = state.get('files_large_documents_ids')[doc_needed_of_file]
        large_documents_ids_len = len(large_documents_ids)
        retriever = config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE.as_retriever(search_type = 'mmr', search_kwargs = {'filter': {'id': {'$in': large_documents_ids}}, 'k': large_documents_ids_len})
        retrieved_docs = retriever.invoke('Fetch All Docs Of Provided File Name')
        sorted_retrieved_docs = sorted(retrieved_docs, key=fetch_doc_index)
        # print('SORTED RETRIEVED DOCS = ', sorted_retrieved_docs)
        files_sorted_docs[doc_needed_of_file] = sorted_retrieved_docs
    return {'all_files_sorted_docs': files_sorted_docs}

class AllDocsRAGResponseSchema(BaseModel):
    answer: str
def generate_all_docs_rag_response(state: RAGGraphState) -> RAGGraphState:
    # print('GENERATING ALL DOCS RAG RESPONSE')
    files_all_sorted_docs = state.get('all_files_sorted_docs')
    files = state.get('docs_needed_of_files')

    queries = state.get('queries')
    question = ''
    for query in queries:
        question += (query + '\n' + 'OR' '\n')
    
    
    first_llm_call = True
    answer = ''
    for file in files:
        # print('FILE DOCS SENDING TO LLM: ', file)
        file_all_sorted_docs = files_all_sorted_docs[file]

        total_sorted_docs = len(file_all_sorted_docs)
        
        chunks_to_send_in_each_llm_call = math.floor(total_sorted_docs/4)
        
        chunks_indexes_to_send_in_each_llm_call = [(0, chunks_to_send_in_each_llm_call), (chunks_to_send_in_each_llm_call, chunks_to_send_in_each_llm_call * 2), (chunks_to_send_in_each_llm_call * 2, chunks_to_send_in_each_llm_call * 3), (chunks_to_send_in_each_llm_call * 3, total_sorted_docs)]        

        # print('TOTAL DOCS IN THIS FILE = ', total_sorted_docs)
        for i in range(0, len(chunks_indexes_to_send_in_each_llm_call)):
            
            # print('LLM CALL NO WITH FILE = ', file, 'AND CALL NO = ', i)
        
            if first_llm_call:
                system_message ="You are an expert research assistant. Draft an initial, detailed answer to the user's question based ONLY on the following text chunk:"
                human_message = "Question: {question}\n\nText Chunk: {text}"    

                current_call_chunk_indexes = chunks_indexes_to_send_in_each_llm_call[i]
                current_call_sorted_docs = file_all_sorted_docs[current_call_chunk_indexes[0]: current_call_chunk_indexes[1]]

                formatted_current_call_docs = ''
                for index, current_call_sorted_doc in enumerate(current_call_sorted_docs):
                    if index == 0:
                        formatted_current_call_docs += f'''FILE NAME: {state.get('files_data_dict').get(file).get('file_name')}
                                                        TITLE: {state.get('files_data_dict').get(file).get('title')}
                                                        AUTHORS: {state.get('files_data_dict').get(file).get('authors')}
                                                        _________________________________________________________________________
                                                        '''
                    formatted_current_call_docs += current_call_sorted_doc.page_content
                
                text = formatted_current_call_docs
                prompt = ChatPromptTemplate(messages=[('system', system_message), ('human', human_message)]).invoke({
                    'question': question,
                    'text': text
                })

                response = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(AllDocsRAGResponseSchema).invoke(prompt)
                answer = response.answer
                # print('INITIAL ANSWER = ', answer)
                first_llm_call = False
                continue
            

            system_message = '''You have an existing answer draft and also a question. Refine and update the existing answer based on the new context provided below."
                **INSTRUCTIONS:**
                1. If the new context adds new information, integrate it logically into the existing answer.
                2. If the new context contradicts or corrects the existing answer, prioritize the new information (as it is later/more specific) but note the source difference if it's crucial.
                3. If the new context is entirely irrelevant, return the existing answer draft unchanged.
                Ensure the final output is a single, complete, synthesized answer.'''
            
            human_message = '''Original Question: {question}"
                Existing Answer Draft:{existing_answer}"
                New Context: {text}'''
            
            current_call_chunk_indexes = chunks_indexes_to_send_in_each_llm_call[i]
            current_call_sorted_docs = file_all_sorted_docs[current_call_chunk_indexes[0]: current_call_chunk_indexes[1]]

            formatted_current_call_docs = ''
            for index, current_call_sorted_doc in enumerate(current_call_sorted_docs):
                if index == 0:
                    formatted_current_call_docs += f'''FILE NAME: {state.get('files_data_dict').get(file).get('file_name')}
                                                    TITLE: {state.get('files_data_dict').get(file).get('title')}
                                                    AUTHORS: {state.get('files_data_dict').get(file).get('authors')}
                                                    _________________________________________________________________________
                                                    '''
                formatted_current_call_docs += current_call_sorted_doc.page_content
            
            text = formatted_current_call_docs

            prompt = ChatPromptTemplate(messages=[('system', system_message), ('human', human_message)]).invoke({
                'question': question,
                'existing_answer': answer,
                'text': text
            })

            response = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(AllDocsRAGResponseSchema).invoke(prompt)
            answer = response.answer
            # print('ANSWER = ', answer)

    return {'answer_provided': True, 'rag_messages': [AIMessage(content = answer, id = str(uuid4()))]}
    

class RAGSummarySchema(BaseModel):
    rag_summary: str = Field(description='summary of conversation between Human and AI.')
def generate_rag_summary(state: RAGGraphState) -> RAGGraphState:
    rag_summary_generation_llm = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(RAGSummarySchema)

    rag_messages = state.get('rag_messages')
    conversation = []
    for rag_message in rag_messages:
        if isinstance(rag_message, AIMessage):
            add_rag_message = ('AI', rag_message.content)
        elif isinstance(rag_message, HumanMessage):
            add_rag_message = ('Human', rag_message.content)
        conversation.append(add_rag_message)

    previous_rag_summary = state.get('rag_summary', '')
    if not previous_rag_summary:
        prompt = f"""Task: Generate a highly condensed and factual summary of the conversation provided below.
                    Goal: The output must serve as a standalone context block for an AI to seamlessly reference past conversation details and accurately answer future user queries.
                    Constraints:
                    Be extremely precise and token-efficient.
                    Include all critical and unique information discussed, such as specific user requirements, decisions made, proper nouns, and key facts.
                    Conversation: {conversation}"""
        rag_summary = rag_summary_generation_llm.invoke(prompt).rag_summary
        rag_messages_to_delete = [RemoveMessage(id = rag_message_to_delete.id) for rag_message_to_delete in rag_messages]
        ai_rag_response = rag_messages[-1]
        return {'rag_summary': rag_summary, 'rag_messages': rag_messages_to_delete, 'ai_rag_response': AIMessage(content = ai_rag_response.content)}

    prompt = f"""Task: Generate a single, updated, and highly compact context summary by synthesizing the provided Previous conversation summary and Current conversation messages.
            Goal: The resulting summary must serve as the definitive and complete context record for future AI reference. It must accurately capture all necessary details, decisions, specific requirements, and facts from the entire dialogue history.
            Instructions for Synthesis:
            Integrate: Incorporate all critical information from the Current conversation messages into the previous summary.
            Refine: Eliminate all redundant, repetitive, or superseded information from the previous summary to maintain maximum token efficiency.
            Density: Ensure the final output is extremely precise and dense with context necessary for future question-answering.
            Previous Context Summary: "{previous_rag_summary}"
            Current Conversation Messages: {conversation}""" 
    rag_summary = rag_summary_generation_llm.invoke(prompt).rag_summary
    rag_messages_to_delete = [RemoveMessage(id = rag_message_to_delete.id) for rag_message_to_delete in rag_messages]
    # print('MESSAGES LIST TO DELETE = ', rag_messages_to_delete)
    ai_rag_response = rag_messages[-1]
    return {'rag_summary': rag_summary, 'rag_messages': rag_messages_to_delete, 'ai_rag_response': AIMessage(content = ai_rag_response.content)}

class QueriesGenerationSchema(BaseModel):
    queries: list[str] = Field(description='list of multiple query generated to retrieve documents in RAG pipeline')

def retrieve_documents(state: RAGGraphState) -> RAGGraphState:

    small_document_ids = state.get('small_document_ids')
    large_document_ids = state.get('large_document_ids')

    if small_document_ids and large_document_ids:
        
        small_docs_retrieval = config_to_load_at_initialization.SMALL_DOCS_VECTOR_STORE.as_retriever(search_type = 'mmr', search_kwargs = {'filter': {'id': {'$in': small_document_ids}}, 'k': 5})
        large_docs_retrieval = config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE.as_retriever(search_type = 'mmr', search_kwargs = {'filter': {'id': {'$in': large_document_ids}}, 'k': 5})

    else:

        small_docs_retrieval = config_to_load_at_initialization.SMALL_DOCS_VECTOR_STORE.as_retriever(search_type = 'mmr', search_kwargs = {'k': 5})
        large_docs_retrieval = config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE.as_retriever(search_type = 'mmr', search_kwargs = {'k': 5})



    merged_docs_retrieval = MergerRetriever(retrievers = [small_docs_retrieval, large_docs_retrieval])
    
    redundant_docs_filter = EmbeddingsRedundantFilter(embeddings=config_to_load_at_initialization.SMALL_EMBEDDING_MODEL)
    docs_reorder = LongContextReorder()

    compressor_pipeline = DocumentCompressorPipeline(transformers = [redundant_docs_filter, docs_reorder])
    merged_contextually_compressed_reordered_docs_retrieval = ContextualCompressionRetriever(base_compressor=compressor_pipeline, base_retriever=merged_docs_retrieval)

    queries = state.get('queries')
    all_docs = []
    for query in queries:
        docs = merged_contextually_compressed_reordered_docs_retrieval.invoke(query)
        for doc in docs:
            all_docs.append(doc)
    return {'retrieved_documents': all_docs}

def remove_similar_documents(state: RAGGraphState) -> RAGGraphState:
    retrieved_docs = state.get('retrieved_documents')
    
    ids_added_in_unique_docs = []
    unique_titles = []
    unique_metadata = []
    unique_docs = []
    for retrieved_doc in retrieved_docs:
        if retrieved_doc.metadata.get('id') not in ids_added_in_unique_docs:
            unique_docs.append(retrieved_doc)
            ids_added_in_unique_docs.append(retrieved_doc.metadata.get('id'))
        if retrieved_doc.metadata.get('title') not in unique_titles:
            unique_titles.append(retrieved_doc.metadata.get('title'))
            metadata = {}
            metadata['title'] = retrieved_doc.metadata.get('title')
            metadata['publication_date'] = retrieved_doc.metadata.get('publication_date')
            metadata['document_type'] = retrieved_doc.metadata.get('document_type')
            metadata['authors'] = retrieved_doc.metadata.get('authors')
            metadata['document_topic'] = retrieved_doc.metadata.get('document_topic')
            unique_metadata.append(metadata)

    formatted_docs = ''
    for (unique_title, metadata) in zip(unique_titles, unique_metadata):
        metadata_to_add_in_formatted_docs = f"\n METADATA ABOUT DOCUMENTS \n TITLE = '{metadata.get('title')}' \n PUBLICATION DATE = {metadata.get('publication_date')} \n AUTHORS = {metadata.get('authors')} \n DOCUMENTS TYPE = {metadata.get('document_type')} \n DOCUMENT TOPIC = {metadata.get('document_topic')}"

        formatted_docs = formatted_docs + '______________________________________________________________________' + '\n' + metadata_to_add_in_formatted_docs

        doc_count = 1
        for unique_doc in unique_docs:
            if unique_doc.metadata.get('title') == unique_title:
                doc_to_add = f"DOCUMENT NUMBER = {doc_count} \n {unique_doc.page_content}"
                formatted_docs = formatted_docs + '--------------------------------------------' + '\n' + doc_to_add
                doc_count = doc_count + 1

    # print('FORMATTED DOCS = ', formatted_docs)
    # print('TOTAL UNIQUE TITLES = ', len(unique_titles))
    # print('TOTAL DOCS = ', len(retrieved_docs))
    # print('UNIQUE DOCS = ', len(unique_docs))

    return {'unique_retrieved_documents': unique_docs, 'formatted_docs': formatted_docs}

class RAGResponseSchema(BaseModel):
    answer_provided: bool = Field(..., description="A boolean indicating whether the model was able to provide an answer **BASED ENTIRELY** on the content of the Retrieved Documents and Past Conversation Summary.")
    answer: Optional[str] = Field('', description="The final answer derived **EXCLUSIVELY** from the provided context. If 'answer_provided' is false, this string **MUST** state that the information is missing from the context.")
def generate_rag_response(state: RAGGraphState) -> RAGGraphState:
    rag_response_generation_llm = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(RAGResponseSchema)

    rag_summary = state.get('rag_summary', 'No Previous Conversation Summary Is Present')
    formatted_docs = state.get('formatted_docs')
    rag_messages = state.get('rag_messages')

    query = rag_messages[0].content
    # print('Sending query = ', query)
    
    system_message = """
                    Role: You are a **Grounded Contextual Synthesis Engine**. Your single source of truth is the provided context.

                    Primary Task: Answer the user's latest question.

                    Core Constraints (Priority Order):
                    1. **Primary Source (Strict Grounding):** You MUST first attempt to answer the question ONLY by citing and combining information found within the **"Retrieved Documents."**
                    2. **Secondary Source (Contextual Use):** Use the **"Past Conversation Summary"** ONLY to resolve ambiguity or provide necessary history if the primary source is insufficient.
                    3. **Synthesis:** You MUST combine and synthesize information found across multiple chunks or sources if necessary to formulate a complete answer.
                    4. **Knowledge Lock & Refusal (CRITICAL):** You **ABSOLUTELY MUST NOT** use any external, prior, or internal knowledge base. If the answer cannot be fully generated using the provided text, you must set 'answer_provided' to **false** and state that the required information is missing from the context.
                    """
    
    human_message = '''  Past Conversation Summary:
                        "{rag_summary}"
    
                        Retrieved Documents:
                        {formatted_docs}

                        Question Asked by Human:
                        {question}'''


    prompt = ChatPromptTemplate(messages = [('system', system_message), ('human', human_message)]).invoke({
        'formatted_docs': formatted_docs,
        'rag_summary': rag_summary,
        'question': query
    }).messages
    # print('PROMPT SENDING TO GENERATE RESPONSE = ', prompt)
    response = rag_response_generation_llm.invoke(prompt)
    answer_provided = response.answer_provided

    if answer_provided:
        answer = response.answer
        return {'answer_provided': answer_provided, 'rag_messages': [AIMessage(content = answer, id = str(uuid4()))]}
    
    return {'answer_provided': answer_provided, 'rag_messages': [AIMessage(id = str(uuid4()), content = 'Insufficient information in provided retrieved documents to answer user question')]}


rag_graph = StateGraph(state_schema=RAGGraphState, input_schema=RAGGraphOutputState, output_schema=RAGGraphOutputState)

rag_graph.add_node('generate_rag_summary', generate_rag_summary)
rag_graph.add_node('generate_queries', generate_queries)
rag_graph.add_node('categorize_question', categorize_question)
rag_graph.add_node('retrieve_all_docs', retrieve_all_docs)
rag_graph.add_node('generate_all_docs_rag_response', generate_all_docs_rag_response)
rag_graph.add_node('retrieve_documents', retrieve_documents)
rag_graph.add_node('remove_similar_documents', remove_similar_documents)
rag_graph.add_node('generate_rag_response', generate_rag_response)

rag_graph.add_edge(START, 'generate_queries')
rag_graph.add_edge('generate_queries', 'categorize_question')
rag_graph.add_conditional_edges('categorize_question', route_rag_question, {'rag_response_route': 'retrieve_documents', 'all_docs_rag_response_route': 'retrieve_all_docs'})

rag_graph.add_edge('retrieve_documents', 'remove_similar_documents')
rag_graph.add_edge('remove_similar_documents', 'generate_rag_response')
rag_graph.add_edge('generate_rag_response', 'generate_rag_summary')

rag_graph.add_edge('retrieve_all_docs', 'generate_all_docs_rag_response')
rag_graph.add_edge('generate_all_docs_rag_response', 'generate_rag_summary')

rag_graph.add_edge('generate_rag_summary', END)









