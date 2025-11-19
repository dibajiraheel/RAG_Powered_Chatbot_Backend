import random
import string



def generate_otp(characters=8):
    digits = string.digits
    otp = ''.join(random.choices(digits, k=characters))
    return otp