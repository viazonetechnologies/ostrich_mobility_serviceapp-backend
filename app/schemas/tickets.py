from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_name: str
    customer_phone: str
    customer_address: str
    product_name: str
    issue_description: str
    status: TicketStatus
    priority: TicketPriority
    scheduled_date: datetime
    assigned_technician_id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total_count: int

class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

class TicketDetailResponse(BaseModel):
    id: int
    ticket_number: str
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_email: Optional[str] = None
    product_name: str
    product_model: Optional[str] = None
    issue_description: str
    status: TicketStatus
    priority: TicketPriority
    scheduled_date: datetime
    assigned_technician_id: int
    technician_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    completion_notes: Optional[str] = None
