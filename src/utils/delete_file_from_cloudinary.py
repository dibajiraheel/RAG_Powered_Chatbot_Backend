import cloudinary
from config import config
from cloudinary.uploader import destroy


cloudinary.config(
    cloud_name = config.cloudinary_cloud_name,
    api_key = config.cloudinary_api_key,
    api_secret = config.cloudinary_api_secret
)


def delete_file_from_cloudinary(public_id) -> bool:
    result = destroy(public_id=public_id, invalidate = True)
    # print('RESULT OF DELETING FILE IN UTILS = ', result)
    if result['result'] == 'ok':
        return True
    return False



















