import bcrypt

def encrypt_password(password: str) -> str:
    encoded_password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(encoded_password, salt)
    # print('ENCODED PASSWORD = ', hashed_password)
    decoded_hashed_password = hashed_password.decode('utf-8')
    # print('DECODDED HASHED PASSWORD = ', decoded_hashed_password)
    return decoded_hashed_password

def verify_password(password: str, hashed_password: str) -> bool:
    encoded_password = password.encode('utf-8')
    # print('HASHED PASSWORD RECEIVED FROM DATABASE = ', hashed_password)
    encoded_hashed_password = hashed_password.encode('utf-8')
    is_password_verified = bcrypt.checkpw(encoded_password, encoded_hashed_password)
    return is_password_verified
