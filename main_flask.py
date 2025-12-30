from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import jwt
from datetime import datetime, timedelta
from functools import wraps
import pymysql
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'service-secret-key')
app.config['SECRET_KEY'] = SECRET_KEY

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'Aru247899!'),
    'database': os.getenv('DB_NAME', 'ostrich_db'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'charset': 'utf8mb4'
}

@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        yield connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        yield None
    finally:
        if connection:
            connection.close()

# JWT utilities
def create_access_token(data):
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

# Auth decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            payload = verify_token(token)
            if payload:
                return f(current_user=payload, *args, **kwargs)
        return jsonify({'error': 'Token required'}), 401
    return decorated

# Routes
@app.route('/')
def read_root():
    return jsonify({
        "message": "Ostrich Service Support API",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "status": "running"
    })

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "ostrich-service-api",
        "environment": os.getenv("ENVIRONMENT", "development")
    })

# ========== AUTHENTICATION ENDPOINTS ==========
@app.route('/api/v1/auth/login', methods=['POST'])
def login_technician():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Demo credentials
    if username == "demo.tech" and password == "password123":
        access_token = create_access_token({"sub": "1", "username": username})
        return jsonify({
            "access_token": access_token,
            "technician_id": 1,
            "full_name": "John Technician",
            "role": "technician"
        })
    
    return jsonify({"detail": "Invalid username or password"}), 401

@app.route('/api/v1/auth/signup', methods=['POST'])
def signup_technician():
    data = request.get_json()
    full_name = data.get('full_name')
    employee_id = data.get('employee_id')
    
    # In production, validate employee_id and create account
    access_token = create_access_token({"sub": "2", "employee_id": employee_id})
    return jsonify({
        "access_token": access_token,
        "technician_id": 2,
        "full_name": full_name,
        "role": "technician"
    })

@app.route('/api/v1/auth/send-otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    contact = data.get('contact')
    
    return jsonify({
        "message": "OTP sent successfully",
        "contact": contact,
        "otp": "123456"  # Demo OTP
    })

@app.route('/api/v1/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp = data.get('otp')
    
    if otp == "123456":
        access_token = create_access_token({"sub": "3", "otp_verified": True})
        return jsonify({
            "access_token": access_token,
            "technician_id": 3,
            "full_name": "OTP Verified Tech",
            "role": "technician"
        })
    
    return jsonify({"detail": "Invalid OTP"}), 400

# ========== DASHBOARD ENDPOINTS ==========
@app.route('/api/v1/dashboard/')
@token_required
def get_dashboard(current_user):
    return jsonify({
        "stats": {
            "assigned_tickets": 8,
            "completed_today": 3,
            "pending_tickets": 5,
            "in_progress": 2,
            "total_completed_this_month": 45
        },
        "recent_tickets": [
            {
                "id": 1,
                "ticket_number": "TKT000001",
                "customer_name": "John Customer",
                "status": "in_progress",
                "priority": "high",
                "scheduled_time": datetime.now().isoformat()
            },
            {
                "id": 2,
                "ticket_number": "TKT000002",
                "customer_name": "Jane Smith",
                "status": "scheduled",
                "priority": "medium",
                "scheduled_time": (datetime.now() + timedelta(hours=2)).isoformat()
            }
        ],
        "performance": {
            "avg_resolution_time": "2.5 hours",
            "customer_rating": 4.7,
            "completion_rate": 95.5
        }
    })

# ========== TICKETS ENDPOINTS ==========
@app.route('/api/v1/tickets/assigned')
@token_required
def get_assigned_tickets(current_user):
    status = request.args.get('status')
    priority = request.args.get('priority')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    tickets = [
        {
            "id": 1,
            "ticket_number": "TKT000001",
            "customer_name": "John Customer",
            "customer_phone": "9876543210",
            "customer_address": "123 Main St, Mumbai, Maharashtra",
            "product_name": "3HP Motor",
            "issue_description": "Motor not starting, making unusual noise",
            "status": "SCHEDULED",
            "priority": "HIGH",
            "scheduled_date": datetime.now().isoformat(),
            "assigned_technician_id": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": 2,
            "ticket_number": "TKT000002",
            "customer_name": "Jane Smith",
            "customer_phone": "9876543211",
            "customer_address": "456 Service Ave, Delhi",
            "product_name": "5HP Pump",
            "issue_description": "Pump not priming properly",
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
            "scheduled_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            "assigned_technician_id": 1,
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    # Apply filters
    if status:
        tickets = [t for t in tickets if t['status'].lower() == status.lower()]
    if priority:
        tickets = [t for t in tickets if t['priority'].lower() == priority.lower()]
    
    # Apply pagination
    total_count = len(tickets)
    tickets = tickets[offset:offset + limit]
    
    return jsonify({
        "tickets": tickets,
        "total_count": total_count
    })

@app.route('/api/v1/tickets/completed')
@token_required
def get_completed_tickets(current_user):
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    tickets = [
        {
            "id": 3,
            "ticket_number": "TKT000003",
            "customer_name": "Bob Wilson",
            "customer_phone": "9876543212",
            "customer_address": "789 Repair Rd, Bangalore",
            "product_name": "7HP Generator",
            "issue_description": "Generator not starting",
            "status": "COMPLETED",
            "priority": "HIGH",
            "scheduled_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "assigned_technician_id": 1,
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "updated_at": (datetime.now() - timedelta(hours=6)).isoformat()
        }
    ]
    
    return jsonify({
        "tickets": tickets[offset:offset + limit],
        "total_count": len(tickets)
    })

@app.route('/api/v1/tickets/<int:ticket_id>')
@token_required
def get_ticket_details(ticket_id, current_user):
    return jsonify({
        "id": ticket_id,
        "ticket_number": "TKT000001",
        "customer_name": "John Customer",
        "customer_phone": "9876543210",
        "customer_address": "123 Main St, Mumbai, Maharashtra",
        "customer_email": "john@example.com",
        "product_name": "3HP Motor",
        "product_model": "OST-3HP-SP",
        "product_serial": "SN123456789",
        "issue_description": "Motor not starting, making unusual noise when attempting to start",
        "status": "SCHEDULED",
        "priority": "HIGH",
        "scheduled_date": datetime.now().isoformat(),
        "assigned_technician_id": 1,
        "technician_name": "John Technician",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "completion_notes": None,
        "customer_signature": None,
        "parts_used": [],
        "work_performed": None,
        "photos": []
    })

@app.route('/api/v1/tickets/<int:ticket_id>/status', methods=['PUT'])
@token_required
def update_ticket_status(ticket_id, current_user):
    data = request.get_json()
    status = data.get('status', '').upper()
    notes = data.get('notes', '')
    work_performed = data.get('work_performed', '')
    parts_used = data.get('parts_used', [])
    
    return jsonify({
        "message": "Ticket status updated successfully",
        "ticket_id": ticket_id,
        "new_status": status,
        "updated_at": datetime.now().isoformat(),
        "notes": notes
    })

@app.route('/api/v1/tickets/<int:ticket_id>/location', methods=['POST'])
@token_required
def capture_location(ticket_id, current_user):
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    
    return jsonify({
        "message": "Location captured successfully",
        "ticket_id": ticket_id,
        "latitude": latitude,
        "longitude": longitude,
        "captured_at": datetime.now().isoformat(),
        "address": "Approximate address based on coordinates"
    })

@app.route('/api/v1/tickets/<int:ticket_id>/photos', methods=['POST'])
@token_required
def upload_ticket_photos(ticket_id, current_user):
    return jsonify({
        "message": "Photos uploaded successfully",
        "ticket_id": ticket_id,
        "photo_count": 3,
        "photo_urls": [
            f"https://example.com/photos/{ticket_id}_1.jpg",
            f"https://example.com/photos/{ticket_id}_2.jpg",
            f"https://example.com/photos/{ticket_id}_3.jpg"
        ]
    })

@app.route('/api/v1/tickets/<int:ticket_id>/signature', methods=['POST'])
@token_required
def capture_signature(ticket_id, current_user):
    return jsonify({
        "message": "Customer signature captured successfully",
        "ticket_id": ticket_id,
        "signature_url": f"https://example.com/signatures/{ticket_id}_signature.png",
        "captured_at": datetime.now().isoformat()
    })

@app.route('/api/v1/tickets/<int:ticket_id>/parts', methods=['POST'])
@token_required
def add_parts_used(ticket_id, current_user):
    data = request.get_json()
    parts = data.get('parts', [])
    
    return jsonify({
        "message": "Parts information updated successfully",
        "ticket_id": ticket_id,
        "parts_added": len(parts),
        "total_cost": sum(part.get('cost', 0) for part in parts)
    })

# ========== NOTIFICATIONS ENDPOINTS ==========
@app.route('/api/v1/notifications/')
@token_required
def get_notifications(current_user):
    return jsonify([
        {
            "id": 1,
            "title": "New Ticket Assigned",
            "message": "You have been assigned ticket TKT000004 for motor repair",
            "type": "info",
            "is_read": False,
            "created_at": datetime.now().isoformat(),
            "ticket_id": 4
        },
        {
            "id": 2,
            "title": "Urgent Ticket",
            "message": "High priority ticket TKT000005 requires immediate attention",
            "type": "urgent",
            "is_read": False,
            "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "ticket_id": 5
        },
        {
            "id": 3,
            "title": "Schedule Update",
            "message": "Your schedule for tomorrow has been updated",
            "type": "info",
            "is_read": True,
            "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
            "ticket_id": None
        }
    ])

@app.route('/api/v1/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(notification_id, current_user):
    return jsonify({
        "message": "Notification marked as read",
        "notification_id": notification_id
    })

@app.route('/api/v1/notifications/unread-count')
@token_required
def get_unread_count(current_user):
    return jsonify({
        "unread_count": 2
    })

# ========== SCHEDULE ENDPOINTS ==========
@app.route('/api/v1/schedule/')
@token_required
def get_schedule(current_user):
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    return jsonify({
        "date": date,
        "appointments": [
            {
                "id": 1,
                "ticket_number": "TKT000001",
                "customer_name": "John Customer",
                "start_time": "09:00",
                "end_time": "11:00",
                "status": "scheduled",
                "address": "123 Main St, Mumbai",
                "priority": "high"
            },
            {
                "id": 2,
                "ticket_number": "TKT000002",
                "customer_name": "Jane Smith",
                "start_time": "14:00",
                "end_time": "16:00",
                "status": "scheduled",
                "address": "456 Service Ave, Delhi",
                "priority": "medium"
            }
        ],
        "total_appointments": 2,
        "working_hours": {
            "start": "08:00",
            "end": "18:00"
        }
    })

# ========== PROFILE ENDPOINTS ==========
@app.route('/api/v1/profile/')
@token_required
def get_profile(current_user):
    return jsonify({
        "id": 1,
        "employee_id": "EMP001",
        "full_name": "John Technician",
        "email": "john.tech@ostrich.com",
        "phone": "9876543220",
        "role": "technician",
        "department": "Field Service",
        "experience_years": 5,
        "specializations": ["Motors", "Pumps", "Generators"],
        "certification_level": "Senior Technician",
        "join_date": "2020-01-15",
        "performance_rating": 4.8,
        "completed_tickets_total": 1250
    })

@app.route('/api/v1/profile/', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    return jsonify({
        "message": "Profile updated successfully",
        "updated_fields": list(data.keys())
    })

# ========== REPORTS ENDPOINTS ==========
@app.route('/api/v1/reports/performance')
@token_required
def get_performance_report(current_user):
    period = request.args.get('period', 'month')  # day, week, month, year
    
    return jsonify({
        "period": period,
        "tickets_completed": 45,
        "avg_resolution_time": "2.5 hours",
        "customer_satisfaction": 4.7,
        "efficiency_score": 92.5,
        "on_time_completion": 95.2,
        "breakdown_by_type": {
            "motor_repair": 20,
            "pump_service": 15,
            "generator_maintenance": 10
        },
        "daily_stats": [
            {"date": "2025-12-01", "completed": 3, "avg_time": "2.2h"},
            {"date": "2025-12-02", "completed": 4, "avg_time": "2.8h"},
            {"date": "2025-12-03", "completed": 2, "avg_time": "1.9h"}
        ]
    })

# ========== INVENTORY ENDPOINTS ==========
@app.route('/api/v1/inventory/')
@token_required
def get_inventory(current_user):
    return jsonify([
        {
            "id": 1,
            "part_number": "BRG001",
            "name": "Motor Bearing",
            "category": "Bearings",
            "quantity_available": 15,
            "unit_cost": 250.0,
            "location": "Van Inventory"
        },
        {
            "id": 2,
            "part_number": "WND001",
            "name": "Motor Winding",
            "category": "Electrical",
            "quantity_available": 5,
            "unit_cost": 1500.0,
            "location": "Warehouse"
        }
    ])

@app.route('/api/v1/inventory/request', methods=['POST'])
@token_required
def request_parts(current_user):
    data = request.get_json()
    parts = data.get('parts', [])
    
    return jsonify({
        "message": "Parts request submitted successfully",
        "request_id": "REQ000123",
        "parts_requested": len(parts),
        "estimated_delivery": "2025-12-12",
        "status": "pending_approval"
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8002))
    app.run(host="0.0.0.0", port=port, debug=False)