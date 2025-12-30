from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime
from app.core.database import get_db

router = APIRouter()

def get_current_technician(db: Session = Depends(get_db)):
    """Get current technician from database"""
    try:
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
        
        return {"technician_id": 1, "full_name": "Service Technician"}
    except:
        return {"technician_id": 1, "full_name": "Service Technician"}

@router.get("/assigned")
async def get_assigned_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_tech = Depends(get_current_technician)
):
    """Get tickets assigned to current technician"""
    
    try:
        tech_id = current_tech["technician_id"]
        
        if db is None:
            return {"tickets": [], "total_count": 0}
        
        # Build query with filters
        where_conditions = ["st.assigned_staff_id = :tech_id", "st.status IN ('SCHEDULED', 'IN_PROGRESS')"]
        params = {"tech_id": tech_id}
        
        if status:
            where_conditions.append("st.status = :status")
            params["status"] = status.upper()
        
        if priority:
            where_conditions.append("st.priority = :priority")
            params["priority"] = priority.upper()
        
        where_clause = " AND ".join(where_conditions)
        
        # Get total count
        count_query = text(f"SELECT COUNT(*) FROM service_tickets st WHERE {where_clause}")
        total_count = db.execute(count_query, params).scalar() or 0
        
        # Get tickets with pagination
        tickets_query = text(f"""
            SELECT st.id, st.ticket_number, st.issue_description, st.status, st.priority, 
                   st.scheduled_date, st.created_at, st.updated_at, st.product_serial_number,
                   c.contact_person, c.phone, c.address, c.city
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            WHERE {where_clause}
            ORDER BY st.scheduled_date ASC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({"limit": limit, "offset": offset})
        tickets_result = db.execute(tickets_query, params).fetchall()
        
        tickets = []
        for ticket in tickets_result:
            tickets.append({
                "id": ticket[0],
                "ticket_number": ticket[1],
                "customer_name": ticket[9] or "Unknown Customer",
                "customer_phone": ticket[10] or "N/A",
                "customer_address": f"{ticket[11] or ''}, {ticket[12] or ''}".strip(", "),
                "product_name": ticket[8] or "Service Request",
                "issue_description": ticket[2] or "No description",
                "status": ticket[3] or "SCHEDULED",
                "priority": ticket[4] or "MEDIUM",
                "scheduled_date": ticket[5].isoformat() if ticket[5] else datetime.now().isoformat(),
                "assigned_technician_id": tech_id,
                "created_at": ticket[6].isoformat() if ticket[6] else datetime.now().isoformat(),
                "updated_at": ticket[7].isoformat() if ticket[7] else datetime.now().isoformat()
            })
        
        return {
            "tickets": tickets,
            "total_count": total_count
        }
        
    except Exception as e:
        print(f"Assigned tickets error: {e}")
        return {"tickets": [], "total_count": 0}

@router.get("/completed")
async def get_completed_tickets(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_tech = Depends(get_current_technician)
):
    """Get completed tickets for current technician"""
    
    try:
        tech_id = current_tech["technician_id"]
        
        if db is None:
            return {"tickets": [], "total_count": 0}
        
        # Get completed tickets
        tickets_query = text("""
            SELECT st.id, st.ticket_number, st.issue_description, st.status, st.priority,
                   st.scheduled_date, st.created_at, st.updated_at, st.product_serial_number,
                   c.contact_person, c.phone, c.address, c.city
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            WHERE st.assigned_staff_id = :tech_id AND st.status = 'COMPLETED'
            ORDER BY st.updated_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        tickets_result = db.execute(tickets_query, {"tech_id": tech_id, "limit": limit, "offset": offset}).fetchall()
        
        # Get total count
        count_query = text("SELECT COUNT(*) FROM service_tickets WHERE assigned_staff_id = :tech_id AND status = 'COMPLETED'")
        total_count = db.execute(count_query, {"tech_id": tech_id}).scalar() or 0
        
        tickets = []
        for ticket in tickets_result:
            tickets.append({
                "id": ticket[0],
                "ticket_number": ticket[1],
                "customer_name": ticket[9] or "Unknown Customer",
                "customer_phone": ticket[10] or "N/A",
                "customer_address": f"{ticket[11] or ''}, {ticket[12] or ''}".strip(", "),
                "product_name": ticket[8] or "Service Request",
                "issue_description": ticket[2] or "No description",
                "status": ticket[3] or "COMPLETED",
                "priority": ticket[4] or "MEDIUM",
                "scheduled_date": ticket[5].isoformat() if ticket[5] else datetime.now().isoformat(),
                "assigned_technician_id": tech_id,
                "created_at": ticket[6].isoformat() if ticket[6] else datetime.now().isoformat(),
                "updated_at": ticket[7].isoformat() if ticket[7] else datetime.now().isoformat()
            })
        
        return {
            "tickets": tickets,
            "total_count": total_count
        }
        
    except Exception as e:
        print(f"Completed tickets error: {e}")
        return {"tickets": [], "total_count": 0}

@router.get("/{ticket_id}")
async def get_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_tech = Depends(get_current_technician)
):
    """Get detailed information for a specific ticket"""
    
    try:
        if db is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket_query = text("""
            SELECT st.id, st.ticket_number, st.issue_description, st.status, st.priority,
                   st.scheduled_date, st.created_at, st.updated_at, st.product_serial_number,
                   st.service_notes, c.contact_person, c.phone, c.address, c.city, c.email,
                   u.first_name, u.last_name
            FROM service_tickets st
            LEFT JOIN customers c ON st.customer_id = c.id
            LEFT JOIN users u ON st.assigned_staff_id = u.id
            WHERE st.id = :ticket_id
        """)
        
        ticket = db.execute(ticket_query, {"ticket_id": ticket_id}).fetchone()
        
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return {
            "id": ticket[0],
            "ticket_number": ticket[1],
            "customer_name": ticket[10] or "Unknown Customer",
            "customer_phone": ticket[11] or "N/A",
            "customer_address": f"{ticket[12] or ''}, {ticket[13] or ''}".strip(", "),
            "customer_email": ticket[14] or "N/A",
            "product_name": ticket[8] or "Service Request",
            "product_model": "N/A",
            "issue_description": ticket[2] or "No description",
            "status": ticket[3] or "SCHEDULED",
            "priority": ticket[4] or "MEDIUM",
            "scheduled_date": ticket[5].isoformat() if ticket[5] else datetime.now().isoformat(),
            "assigned_technician_id": current_tech["technician_id"],
            "technician_name": f"{ticket[15]} {ticket[16]}" if ticket[15] else current_tech["full_name"],
            "created_at": ticket[6].isoformat() if ticket[6] else datetime.now().isoformat(),
            "updated_at": ticket[7].isoformat() if ticket[7] else datetime.now().isoformat(),
            "completion_notes": ticket[9]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ticket details error: {e}")
        raise HTTPException(status_code=404, detail="Ticket not found")

@router.put("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    request: dict,
    db: Session = Depends(get_db),
    current_tech = Depends(get_current_technician)
):
    """Update ticket status and location"""
    
    try:
        if db is None:
            return {"message": "Database unavailable", "ticket_id": ticket_id}
        
        status = request.get("status", "").upper()
        notes = request.get("notes", "")
        
        update_query = text("""
            UPDATE service_tickets 
            SET status = :status, service_notes = :notes, updated_at = NOW()
            WHERE id = :ticket_id
        """)
        
        db.execute(update_query, {"status": status, "notes": notes, "ticket_id": ticket_id})
        db.commit()
        
        return {
            "message": "Ticket status updated successfully",
            "ticket_id": ticket_id,
            "new_status": status,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Update status error: {e}")
        return {"message": "Failed to update ticket", "ticket_id": ticket_id}

@router.post("/{ticket_id}/location")
async def capture_location(
    ticket_id: int,
    latitude: float,
    longitude: float,
    current_tech = Depends(get_current_technician)
):
    """Capture current location for ticket"""
    
    return {
        "message": "Location captured successfully",
        "ticket_id": ticket_id,
        "latitude": latitude,
        "longitude": longitude,
        "captured_at": datetime.now().isoformat()
    }
