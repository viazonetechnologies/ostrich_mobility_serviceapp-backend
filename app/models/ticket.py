from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base

class ServiceTicket(Base):
    __tablename__ = "service_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True)
    customer_name = Column(String(100))
    customer_phone = Column(String(15))
    customer_email = Column(String(100))
    customer_address = Column(Text)
    product_name = Column(String(100))
    product_model = Column(String(50))
    issue_description = Column(Text)
    status = Column(String(20), default="pending")
    priority = Column(String(10), default="medium")
    assigned_technician_id = Column(Integer, ForeignKey("technicians.id"))
    scheduled_date = Column(DateTime(timezone=True))
    latitude = Column(Float)
    longitude = Column(Float)
    completion_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
