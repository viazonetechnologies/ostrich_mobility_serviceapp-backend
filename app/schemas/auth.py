from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class TechnicianLoginRequest(BaseModel):
    username: str
    password: str

class TechnicianSignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    mobile: str
    password: str
    employee_id: Optional[str] = None
    
    @validator('mobile')
    def validate_mobile(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('Mobile number must be 10 digits')
        return v

class SendOTPRequest(BaseModel):
    contact: str  # phone or email

class VerifyOTPRequest(BaseModel):
    contact: str
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    technician_id: int
    full_name: str
    role: str
