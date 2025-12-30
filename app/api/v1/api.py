from fastapi import APIRouter
from .endpoints import auth, dashboard, tickets, notifications

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
