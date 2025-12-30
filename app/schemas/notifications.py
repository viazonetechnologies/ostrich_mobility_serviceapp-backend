from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_UPDATED = "ticket_updated"
    SYSTEM_MESSAGE = "system_message"
    REMINDER = "reminder"

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime
    ticket_id: Optional[int] = None

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int

class MarkNotificationReadRequest(BaseModel):
    notification_ids: List[int]
