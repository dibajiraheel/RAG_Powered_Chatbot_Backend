from pydantic import BaseModel




class VerifyOtp(BaseModel):
    email: str
    otp: str


    








    