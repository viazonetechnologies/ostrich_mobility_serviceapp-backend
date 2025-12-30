from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.core.database import get_db

router = APIRouter()

def get_current_technician(db: Session = Depends(get_db)):
    """Get current technician from database"""
    try:
        # In production, extract from JWT token
        # For now, get first service staff from database
        # First try service_staff
        tech_query = text("SELECT id, first_name, last_name FROM users WHERE role = 'service_staff' LIMIT 1")
        tech_result = db.execute(tech_query).fetchone()
        
        if tech_result:
            return {
                "technician_id": tech_result[0],
                "full_name": f"{tech_result[1]} {tech_result[2]}"
            }
        
        # If no service_staff, get any user from database
        any_user_query = text("SELECT id, first_name, last_name FROM users LIMIT 1")
        any_user_result = db.execute(any_user_query).fetchone()
        
        if any_user_result:
            return {
                "technician_id": any_user_result[0],
                "full_name": f"{any_user_result[1]} {any_user_result[2]}"
            }
        
        # Final fallback
        return {"technician_id": 1, "full_name": "Service Technician"}
    except:
        return {"technician_id": 1, "full_name": "Service Technician"}

@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db), current_tech = Depends(get_current_technician)):
    """Get service technician dashboard overview"""
    
    try:
        tech_id = current_tech["technician_id"]
        
        if db is None:
            return {
                "technician_name": "Service Technician",
                "technician_id": tech_id,
                "stats": {"total_assigned": 0, "pending_tickets": 0, "in_progress_tickets": 0, "completed_today": 0},
                "assigned_tickets": [],
                "recent_completed": []
            }
        
        # Get ticket counts
        pending_count = db.execute(text("SELECT COUNT(*) FROM service_tickets WHERE assigned_staff_id = :tech_id AND status = 'SCHEDULED'"), {"tech_id": tech_id}).scalar() or 0
        in_progress_count = db.execute(text("SELECT COUNT(*) FROM service_tickets WHERE assigned_staff_id = :tech_id AND status = 'IN_PROGRESS'"), {"tech_id": tech_id}).scalar() or 0
        completed_today = db.execute(text("SELECT COUNT(*) FROM service_tickets WHERE assigned_staff_id = :tech_id AND status = 'COMPLETED' AND DATE(updated_at) = CURDATE()"), {"tech_id": tech_id}).scalar() or 0
        
        # Get assigned tickets
        assigned_tickets_query = text("""
            SELECT st.id, st.ticket_number, st.issue_description, st.status, st.priority, st.scheduled_date, st.created_at, st.updated_at,
                   c.contact_person, c.phone, c.address, c.city
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            WHERE st.assigned_staff_id = :tech_id AND st.status IN ('SCHEDULED', 'IN_PROGRESS')
            ORDER BY st.scheduled_date ASC
            LIMIT 5
        """)
        
        assigned_result = db.execute(assigned_tickets_query, {"tech_id": tech_id}).fetchall()
        
        assigned_tickets = []
        for ticket in assigned_result:
            assigned_tickets.append({
                "id": ticket[0],
                "ticket_number": ticket[1],
                "customer_name": ticket[8] or "Unknown Customer",
                "customer_phone": ticket[9] or "N/A",
                "customer_address": f"{ticket[10] or ''}, {ticket[11] or ''}".strip(", "),
                "product_name": "Service Request",
                "issue_description": ticket[2] or "No description",
                "status": ticket[3] or "SCHEDULED",
                "priority": ticket[4] or "MEDIUM",
                "scheduled_date": ticket[5].isoformat() if ticket[5] else datetime.now().isoformat(),
                "assigned_technician_id": tech_id,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "distance_km": 2.5,
                "created_at": ticket[6].isoformat() if ticket[6] else datetime.now().isoformat(),
                "updated_at": ticket[7].isoformat() if ticket[7] else datetime.now().isoformat()
            })
        
        # Get technician name from database
        tech_query = text("SELECT first_name, last_name FROM users WHERE id = :tech_id")
        tech_result = db.execute(tech_query, {"tech_id": tech_id}).fetchone()
        tech_name = f"{tech_result[0]} {tech_result[1]}" if tech_result else f"Technician {tech_id}"
        
        # Get recent completed tickets
        completed_query = text("""
            SELECT st.id, st.ticket_number, st.issue_description, st.updated_at,
                   c.contact_person
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            WHERE st.assigned_staff_id = :tech_id AND st.status = 'COMPLETED'
            ORDER BY st.updated_at DESC
            LIMIT 3
        """)
        
        completed_result = db.execute(completed_query, {"tech_id": tech_id}).fetchall()
        
        recent_completed = []
        for ticket in completed_result:
            recent_completed.append({
                "id": ticket[0],
                "ticket_number": ticket[1],
                "customer_name": ticket[4] or "Unknown Customer",
                "issue_description": ticket[2] or "No description",
                "completed_at": ticket[3].isoformat() if ticket[3] else datetime.now().isoformat()
            })
        
        return {
            "technician_name": tech_name,
            "technician_id": tech_id,
            "stats": {
                "total_assigned": pending_count + in_progress_count,
                "pending_tickets": pending_count,
                "in_progress_tickets": in_progress_count,
                "completed_today": completed_today
            },
            "assigned_tickets": assigned_tickets,
            "recent_completed": recent_completed
        }
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return {
            "technician_name": current_tech["full_name"],
            "technician_id": current_tech["technician_id"],
            "stats": {"total_assigned": 0, "pending_tickets": 0, "in_progress_tickets": 0, "completed_today": 0},
            "assigned_tickets": [],
            "recent_completed": []
        }
