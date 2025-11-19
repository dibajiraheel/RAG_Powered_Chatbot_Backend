from dotenv import load_dotenv
from os import getenv


load_dotenv()

class Config():
    access_token_secret = getenv('ACCESS_TOKEN_SECRET')
    refresh_token_secret = getenv('REFRESH_TOKEN_SECRET')
    access_token_expiry_time_in_minutes = getenv('ACCESS_TOKEN_EXPIRY_TIME_IN_MINUTES')
    refresh_token_expiry_time_in_minutes = getenv('REFRESH_TOKEN_EXPIRY_TIME_IN_MINUTES')
    add_documents_queue = getenv('ADD_DOCUMENTS_QUEUE')
    added_documents_set = getenv('ADDED_DOCUMENTS_SET')
    otp_gmail = getenv('OTP_GMAIL')
    otp_gmail_app_password = getenv('OTP_GMAIL_APP_PASSWORD')
    cloudinary_cloud_name = getenv('CLOUDINARY_CLOUD_NAME')
    cloudinary_api_key = getenv('CLOUDINARY_API_KEY')
    cloudinary_api_secret = getenv('CLOUDINARY_API_SECRET')
    cloudinary_profile_pic_folder_path = getenv('CLOUDINARY_PROFILE_PIC_FOLDER_PATH')
    neon_postgresql_db_url = getenv('NEON_POSTGRESQL_DB_URL')
    min_db_connection = getenv('MIN_DB_CONNECTION')
    max_db_connection = getenv('MAX_DB_CONNECTION')
    small_vector_store_collection_name = getenv('SMALL_VECTOR_STORE_COLLECTION_NAME')
    large_vector_store_colletion_name = getenv('LARGE_VECTOR_STORE_COLLECTION_NAME')
    openai_embedding_model_name = getenv('OPENAI_EMBEDDING_MODEL_NAME')
    openai_chat_model_name = getenv('OPENAI_CHAT_MODEL_NAME')
    frontend_url = getenv('FRONTEND_URL')


config = Config()