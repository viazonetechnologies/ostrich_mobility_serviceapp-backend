from fastapi import APIRouter, Depends
from datetime import datetime, timedelta
from app.schemas.notifications import (
    NotificationListResponse, NotificationResponse, 
    MarkNotificationReadRequest, NotificationType
)

router = APIRouter()

def get_current_technician():
    """Mock authentication - replace with real JWT validation"""
    return {"technician_id": 1, "full_name": "John Technician"}

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(current_tech = Depends(get_current_technician)):
    """Get notifications for current technician"""
    
    # Mock notifications - replace with database queries
    notifications = [
        NotificationResponse(
            id=1,
            title="New Ticket Assigned",
            message="You have been assigned a new high priority ticket #TKT-104 for a PowerPro Wheelchair repair.",
            type=NotificationType.TICKET_ASSIGNED,
            is_read=False,
            created_at=datetime.now() - timedelta(minutes=10),
            ticket_id=104
        ),
        NotificationResponse(
            id=2,
            title="Message from Regional Officer",
            message="Please ensure all completed tickets have location verification before closing.",
            type=NotificationType.SYSTEM_MESSAGE,
            is_read=False,
            created_at=datetime.now() - timedelta(hours=2),
            ticket_id=None
        ),
        NotificationResponse(
            id=3,
            title="Service Reminder",
            message="Don't forget to complete the safety checklist for all motor-related repairs.",
            type=NotificationType.REMINDER,
            is_read=True,
            created_at=datetime.now() - timedelta(days=1),
            ticket_id=None
        ),
        NotificationResponse(
            id=4,
            title="Schedule Update",
            message="Your schedule for tomorrow has been updated. Check your assigned tickets.",
            type=NotificationType.SYSTEM_MESSAGE,
            is_read=True,
            created_at=datetime.now() - timedelta(days=2),
            ticket_id=None
        )
    ]
    
    unread_count = len([n for n in notifications if not n.is_read])
    
    return NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count
    )

@router.post("/mark-read")
async def mark_notifications_read(
    request: MarkNotificationReadRequest,
    current_tech = Depends(get_current_technician)
):
    """Mark notifications as read"""
    
    return {
        "message": f"Marked {len(request.notification_ids)} notifications as read",
        "notification_ids": request.notification_ids,
        "updated_at": datetime.now()
    }

@router.get("/unread-count")
async def get_unread_count(current_tech = Depends(get_current_technician)):
    """Get count of unread notifications"""
    
    return {"unread_count": 2}
