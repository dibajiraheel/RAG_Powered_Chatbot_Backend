import cloudinary
from cloudinary.uploader import upload
from config import config
from os.path import exists
from os import remove


cloudinary.config(
    cloud_name = config.cloudinary_cloud_name,
    api_key = config.cloudinary_api_key,
    api_secret = config.cloudinary_api_secret
)


def upload_file_on_cloudinary(file_path: str):
    response = upload(file = file_path, folder = config.cloudinary_profile_pic_folder_path)
    # print('REMOVE = ', file_path)
    if exists(file_path):
        print('REMOVING')
        remove(file_path)
        print('REMOVED')
    return response









