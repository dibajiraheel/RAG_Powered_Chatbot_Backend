from fastapi import APIRouter, Depends, status, Request, HTTPException, UploadFile, File
from controller.documents.add_document import add_document_controller
from api_models.response import APIResponse
from routes.user_routes import get_user_details
from utils.tokens_model import TokenData
from sqlalchemy.orm import Session
from controller.documents.user_documents import user_documents_controller
from controller.documents.delete_document import delete_document_controller

from files_to_load.config_to_load import get_db_session


document_routes = APIRouter()


@document_routes.post('/add-document', status_code=status.HTTP_200_OK)
async def add_document(file: UploadFile = File(), userinfo: TokenData = Depends(get_user_details) , session: Session = Depends(get_db_session)) -> APIResponse:
    if (file.content_type == 'application/pdf'):
        response = await add_document_controller(file=file, userinfo=userinfo, session=session)
        return response

@document_routes.get('/add-document-status/{job_id}', status_code=status.HTTP_200_OK)
async def add_document_status(job_id: str, userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)):
    if userinfo and job_id:
        response = await add_document_status_controller(job_id = job_id, userinfo = userinfo, session = session)
        return response

@document_routes.get('/user-documents', status_code=status.HTTP_200_OK)
async def user_documents(userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)):
    if userinfo:
        response = await user_documents_controller(userinfo = userinfo, session = session)
        return response

@document_routes.delete('/delete-document/{file_id}', status_code=status.HTTP_200_OK)
async def delete_document(file_id: str, userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)):
    response = await delete_document_controller(file_id=int(file_id), userinfo=userinfo, session=session)
    return response








