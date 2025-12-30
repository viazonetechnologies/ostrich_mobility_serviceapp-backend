from pydantic import BaseModel
from typing import List
from .tickets import TicketResponse

class DashboardStats(BaseModel):
    total_assigned: int
    pending_tickets: int
    in_progress_tickets: int
    completed_today: int

class DashboardResponse(BaseModel):
    technician_name: str
    technician_id: int
    stats: DashboardStats
    assigned_tickets: List[TicketResponse]
    recent_completed: List[TicketResponse]
