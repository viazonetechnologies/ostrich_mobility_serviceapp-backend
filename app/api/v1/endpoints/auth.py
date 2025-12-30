from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import (
    TechnicianLoginRequest, TechnicianSignupRequest, 
    SendOTPRequest, VerifyOTPRequest, AuthResponse
)

router = APIRouter()

@router.post("/login", response_model=AuthResponse)
async def login_technician(request: TechnicianLoginRequest):
    """Login service technician with username/password"""
    
    # Demo credentials
    if request.username == "demo.tech" and request.password == "password123":
        return AuthResponse(
            access_token="demo_service_token_12345",
            technician_id=1,
            full_name="John Technician",
            role="technician"
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password"
    )

@router.post("/signup", response_model=AuthResponse)
async def signup_technician(request: TechnicianSignupRequest):
    """Register new service technician"""
    
    # In production, validate employee_id and create account
    return AuthResponse(
        access_token="new_service_token_67890",
        technician_id=2,
        full_name=request.full_name,
        role="technician"
    )

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest):
    """Send OTP to technician's contact"""
    
    return {
        "message": "OTP sent successfully",
        "contact": request.contact,
        "otp": "123456"  # Demo OTP
    }

@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and authenticate technician"""
    
    if request.otp == "123456":
        return AuthResponse(
            access_token="otp_verified_token_54321",
            technician_id=3,
            full_name="OTP Verified Tech",
            role="technician"
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid OTP"
    )
