from fastapi import UploadFile
import tempfile
import shutil
import os

from utils.tokens_model import TokenData
from api_models.response import APIResponse

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from uuid import uuid4
from db_models.user_model import User
from db_models.file_model import File
import os
from utils.tokens_model import TokenData
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from sqlalchemy.orm import Session

import files_to_load.config_to_load as config_to_load_at_initialization


small_splitter = RecursiveCharacterTextSplitter(chunk_size = 200, chunk_overlap = 50)
large_splitter = RecursiveCharacterTextSplitter(chunk_size = 800, chunk_overlap = 150)


class MetadataToGenerate(BaseModel):
    title: str = Field(..., description="The main title of the document, as extracted from the first page.")
    authors: List[str] = Field(..., description="The main author/authors or organization responsible for the document.")
    document_type: Literal['Research Paper', 'Technical Manual', 'Legal Memo', 'Internal Report', 'Other'] = Field(
        ..., 
        description="The category of the document to aid in filtering and LLM context setting."
    )
    document_topic: str = Field(
        ..., 
        description="A concise summary (less than 15 words) of the document's main subject area."
    )
    publication_date: Optional[str] = Field(
        None, 
        description="The year or full date the document was published or created (e.g., '2023' or '2023-10-14')."
    )


async def add_document_controller(file: UploadFile, userinfo: TokenData, session: Session ) ->  APIResponse:
    
    try:
        temp_file_directory = (str(os.getcwd()) + '/temp_files')
        os.makedirs(temp_file_directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=temp_file_directory, suffix='.pdf', delete=False) as temp_file:
            # copy file in temp_file
            shutil.copyfileobj(file.file, temp_file)
        temp_file_name = (temp_file.name).split("\\")[-1]
        original_file_name = file.filename

        temp_file_path = os.path.join(os.getcwd(), 'temp_files', temp_file_name)
        pdf = PyPDFLoader(file_path = temp_file_path).load()
            
        # generate metadata for file using llm
        text_pdf = ''
        pages_added_in_pdf_text = 0
        for page in pdf:
            if pages_added_in_pdf_text >= 5:
                break
            text_pdf = text_pdf + page.page_content
            pages_added_in_pdf_text += 1


        prompt = ChatPromptTemplate(messages = [('system', 'You have been provided with the text from the pdf document and you have to generate metadata for this pdf in the required format. The generated metadata will be used in future by rag based llm to answer user question so be try to be correct and accurate with what you generate. \n {text_pdf}')]).invoke({
        'text_pdf': text_pdf}) 

        # split temp file in small and large docs
        small_splitted_docs = small_splitter.split_documents(pdf)
        large_splitted_docs = large_splitter.split_documents(pdf)

        
        generated_metadata = config_to_load_at_initialization.LLM_OPENAI.with_structured_output(MetadataToGenerate).invoke(prompt)
        
        # # add id to each doc's metadata in small and large splitted docs
        small_docs_ids = [str(uuid4()) for i in range(0, len(small_splitted_docs))]
        large_docs_ids = [str(uuid4()) for i in range(0, len(large_splitted_docs))]

        small_splitted_docs_with_ids_in_metadata = []
        for index, doc in enumerate(small_splitted_docs):
            doc.metadata['id'] = small_docs_ids[index]
            doc.metadata['title'] = generated_metadata.title
            doc.metadata['authors'] = generated_metadata.authors
            doc.metadata['document_type'] = generated_metadata.document_type
            doc.metadata['document_topic'] = generated_metadata.document_topic
            doc.metadata['publication_date'] = generated_metadata.publication_date
            doc.metadata['order_id'] = index + 1
            small_splitted_docs_with_ids_in_metadata.append(doc)

        large_splitted_docs_with_ids_in_metadata = []
        for index, doc in enumerate(large_splitted_docs):
            doc.metadata['id'] = large_docs_ids[index]
            doc.metadata['title'] = generated_metadata.title
            doc.metadata['authors'] = generated_metadata.authors
            doc.metadata['document_type'] = generated_metadata.document_type
            doc.metadata['document_topic'] = generated_metadata.document_topic
            doc.metadata['publication_date'] = generated_metadata.publication_date
            doc.metadata['order_id'] = index + 1
            large_splitted_docs_with_ids_in_metadata.append(doc)

        # print('TOTAL SMALL DOCS = ', len(small_splitted_docs_with_ids_in_metadata))
        # print('TOTAL LARGE DOCS = ', len(large_splitted_docs_with_ids_in_metadata))
        # add both small and large splitted docs to vector store
        config_to_load_at_initialization.SMALL_DOCS_VECTOR_STORE.add_documents(documents=small_splitted_docs_with_ids_in_metadata, ids=small_docs_ids)
        # print('SMALL DOCS ADDED')
        config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE.add_documents(documents=large_splitted_docs_with_ids_in_metadata, ids=large_docs_ids)
        # print('LARGE DOCS ADDED')

        # add file details in database
        userdata = session.query(User).filter_by(email = userinfo.email).first()


        new_file = File(file_name = original_file_name, small_document_ids = small_docs_ids, large_document_ids = large_docs_ids, user = userdata, title = generated_metadata.title, authors = generated_metadata.authors, document_type = generated_metadata.document_type, document_topic = generated_metadata.document_topic, publication_date = generated_metadata.publication_date)
        session.add(new_file)
        session.commit()   


        filesdata = session.query(File).filter_by(user_id = userdata.id).all()
        if not filesdata:
            response = APIResponse(task_completed=True, detail='no file found', status_code=400)
        
        files_to_send = []
        for filedata in filesdata:
            file_to_send = {'id': filedata.id, 'filename': filedata.file_name}
            files_to_send.append(file_to_send)

        # print('FILE TO DELETE FROM PATH = ', temp_file_path)
        # print('TOTAL = ', os.listdir(temp_file_directory))
        if (os.path.exists(temp_file_path)):
            print('DELETING')
            os.remove(temp_file_path)
            print('DELETED')
            response = APIResponse(task_completed=True, detail=['added in vector store and file deleted successfully', files_to_send], status_code=200)
            return response
        
        response = APIResponse(task_completed=True, detail=['added in vector store and file deletion failed', files_to_send], status_code=200)
        return response

    except Exception as e:
        response = APIResponse(task_completed=False, detail=f'failed to add in vector store \n {e}', status_code=500)    
        return response
    


