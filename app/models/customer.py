from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class CustomerType(str, enum.Enum):
    B2C = "b2c"
    B2B = "b2b"
    B2G = "b2g"

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_code = Column(String(20), unique=True, index=True)
    customer_type = Column(Enum(CustomerType))
    company_name = Column(String(200))
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(15))
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pin_code = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
