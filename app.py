from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import jwt
from functools import wraps
import pymysql
import os
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SECRET_KEY'] = SECRET_KEY

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'your_database_host'),
    'user': os.getenv('DB_USER', 'your_database_user'),
    'password': os.getenv('DB_PASSWORD', 'your_database_password'),
    'database': os.getenv('DB_NAME', 'ostrich'),
    'port': int(os.getenv('DB_PORT', 16599)),
    'ssl_disabled': False,
    'charset': 'utf8mb4'
}

@contextmanager
def get_db_connection():
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        yield connection
    except Exception as e:
        print(f"Database error: {e}")
        if connection:
            connection.rollback()
        yield None
    finally:
        if connection:
            connection.close()

# In-memory storage for demo
technicians = {
    "demo.tech": {"id": 1, "name": "John Technician", "password": "password123"}
}
tickets = []

# JWT utilities
def create_access_token(data):
    payload = data.copy()
    payload['exp'] = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
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
                return f(current_tech=payload, *args, **kwargs)
        return jsonify({'error': 'Token required'}), 401
    return decorated

# Health check
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "ostrich-service-api"})

# Auth endpoints
@app.route('/api/v1/auth/login', methods=['POST'])
def login_technician():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == "demo.tech" and password == "password123":
        return jsonify({
            "access_token": "demo_service_token_12345",
            "technician_id": 1,
            "full_name": "John Technician",
            "role": "technician"
        })
    
    return jsonify({"detail": "Invalid username or password"}), 401

@app.route('/api/v1/auth/signup', methods=['POST'])
def signup_technician():
    data = request.get_json()
    full_name = data.get('full_name')
    
    return jsonify({
        "access_token": "new_service_token_67890",
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
        "otp": "123456"
    })

@app.route('/api/v1/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp = data.get('otp')
    
    if otp == "123456":
        return jsonify({
            "access_token": "otp_verified_token_54321",
            "technician_id": 3,
            "full_name": "OTP Verified Tech",
            "role": "technician"
        })
    
    return jsonify({"detail": "Invalid OTP"}), 400

# Dashboard endpoints
@app.route('/api/v1/dashboard/overview')
def get_dashboard_overview():
    return jsonify({
        "technician_name": "Service Technician",
        "technician_id": 1,
        "stats": {
            "total_assigned": 5,
            "pending_tickets": 3,
            "in_progress_tickets": 2,
            "completed_today": 1
        },
        "assigned_tickets": [
            {
                "id": 1,
                "ticket_number": "TKT000001",
                "customer_name": "John Doe",
                "customer_phone": "9876543210",
                "customer_address": "123 Main St, City",
                "product_name": "Service Request",
                "issue_description": "Motor not starting",
                "status": "SCHEDULED",
                "priority": "HIGH",
                "scheduled_date": datetime.now().isoformat(),
                "assigned_technician_id": 1,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "distance_km": 2.5,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ],
        "recent_completed": [
            {
                "id": 2,
                "ticket_number": "TKT000002",
                "customer_name": "Jane Smith",
                "issue_description": "Routine maintenance",
                "completed_at": datetime.now().isoformat()
            }
        ]
    })

# Tickets endpoints
@app.route('/api/v1/tickets/assigned')
def get_assigned_tickets():
    status = request.args.get('status')
    priority = request.args.get('priority')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    sample_tickets = [
        {
            "id": 1,
            "ticket_number": "TKT000001",
            "customer_name": "John Doe",
            "customer_phone": "9876543210",
            "customer_address": "123 Main St, City",
            "product_name": "3HP Motor",
            "issue_description": "Motor not starting",
            "status": "SCHEDULED",
            "priority": "HIGH",
            "scheduled_date": datetime.now().isoformat(),
            "assigned_technician_id": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    return jsonify({
        "tickets": sample_tickets[:limit],
        "total_count": len(sample_tickets)
    })

@app.route('/api/v1/tickets/completed')
def get_completed_tickets():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    
    sample_tickets = [
        {
            "id": 2,
            "ticket_number": "TKT000002",
            "customer_name": "Jane Smith",
            "customer_phone": "9876543211",
            "customer_address": "456 Oak Ave, Town",
            "product_name": "5HP Motor",
            "issue_description": "Routine maintenance",
            "status": "COMPLETED",
            "priority": "MEDIUM",
            "scheduled_date": datetime.now().isoformat(),
            "assigned_technician_id": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    return jsonify({
        "tickets": sample_tickets[:limit],
        "total_count": len(sample_tickets)
    })

@app.route('/api/v1/tickets/<int:ticket_id>')
def get_ticket_details(ticket_id):
    return jsonify({
        "id": ticket_id,
        "ticket_number": f"TKT{ticket_id:06d}",
        "customer_name": "John Doe",
        "customer_phone": "9876543210",
        "customer_address": "123 Main St, City",
        "customer_email": "john@example.com",
        "product_name": "3HP Motor",
        "product_model": "OST-3HP",
        "issue_description": "Motor not starting",
        "status": "SCHEDULED",
        "priority": "HIGH",
        "scheduled_date": datetime.now().isoformat(),
        "assigned_technician_id": 1,
        "technician_name": "John Technician",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "completion_notes": None
    })

@app.route('/api/v1/tickets/<int:ticket_id>/status', methods=['PUT'])
def update_ticket_status(ticket_id):
    data = request.get_json()
    status = data.get('status', '').upper()
    notes = data.get('notes', '')
    
    return jsonify({
        "message": "Ticket status updated successfully",
        "ticket_id": ticket_id,
        "new_status": status,
        "updated_at": datetime.now().isoformat()
    })

@app.route('/api/v1/tickets/<int:ticket_id>/location', methods=['POST'])
def capture_location(ticket_id):
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    return jsonify({
        "message": "Location captured successfully",
        "ticket_id": ticket_id,
        "latitude": latitude,
        "longitude": longitude,
        "captured_at": datetime.now().isoformat()
    })

# Notifications endpoints
@app.route('/api/v1/notifications/')
def get_notifications():
    return jsonify({
        "notifications": [
            {
                "id": 1,
                "title": "New Ticket Assigned",
                "message": "You have been assigned a new service ticket",
                "type": "assignment",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "is_read": False
            }
        ],
        "unread_count": 1
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True)
