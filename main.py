from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields, Namespace
import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
import pymysql
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app first
app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Add root route before API setup
@app.route('/')
def api_root():
    """Root endpoint - API information"""
    return jsonify({
        "message": "Ostrich Service Technician API",
        "status": True,
        "data": {
            "version": "1.0.0",
            "docs": "/docs/",
            "endpoints": {
                "swagger_ui": "/docs/",
                "health": "/health",
                "auth": "/auth/",
                "dashboard": "/dashboard/",
                "tickets": "/tickets/",
                "notifications": "/notifications/",
                "schedule": "/schedule/",
                "profile": "/profile/",
                "reports": "/reports/",
                "inventory": "/inventory/"
            }
        }
    })

@app.route('/health')
def health_check():
    return jsonify({
        "message": "Service is healthy",
        "status": True,
        "data": {
            "service": "ostrich-service-api",
            "timestamp": datetime.now().isoformat()
        }
    })

# Swagger API setup with comprehensive documentation
api = Api(app, 
    version='1.0', 
    title='Ostrich Service Technician API',
    description='Complete API for Service Technician Mobile App - Test all endpoints with Swagger UI',
    doc='/docs/',
    prefix='/api/v1',  # Add API prefix
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Add "Bearer " before your JWT token'
        }
    },
    security='Bearer'
)

# Namespaces
auth_ns = api.namespace('auth', description='Authentication Operations')
dashboard_ns = api.namespace('dashboard', description='Dashboard & Overview')
tickets_ns = api.namespace('tickets', description='Service Tickets Management')
notifications_ns = api.namespace('notifications', description='Notifications')
schedule_ns = api.namespace('schedule', description='Schedule & Calendar')
profile_ns = api.namespace('profile', description='Technician Profile')
reports_ns = api.namespace('reports', description='Reports & Analytics')
inventory_ns = api.namespace('inventory', description='Parts & Inventory')

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SECRET_KEY'] = SECRET_KEY

# Database configuration - Use environment variables for production
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql-ostrich-tviazone-5922.i.aivencloud.com'),
    'user': os.getenv('DB_USER', 'avnadmin'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'defaultdb'),
    'port': int(os.getenv('DB_PORT', 16599)),
    'charset': 'utf8mb4',
    'ssl': {'ssl_mode': 'REQUIRED'}
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
    payload['exp'] = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]
                payload = verify_token(token)
                if payload:
                    return f(current_user=payload, *args, **kwargs)
            return {'message': 'Token required', 'status': False, 'data': None}, 401
        except Exception as e:
            return {'message': 'Authentication failed', 'status': False, 'data': None}, 401
    return decorated

# ==================== MODELS ====================
# Auth Models
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Technician username', example='demo.tech'),
    'password': fields.String(required=True, description='Password', example='password123')
})

# Signup model removed - service staff don't self-register

otp_model = api.model('SendOTP', {
    'contact': fields.String(required=True, description='Phone number', example='9876543210')
})

verify_otp_model = api.model('VerifyOTP', {
    'contact': fields.String(required=True, description='Phone number', example='9876543210'),
    'otp': fields.String(required=True, description='OTP code', example='123456')
})

# Ticket Models
ticket_status_model = api.model('TicketStatus', {
    'status': fields.String(required=True, description='New status', enum=['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'], example='IN_PROGRESS'),
    'notes': fields.String(required=False, description='Status update notes', example='Started working on the motor'),
    'work_performed': fields.String(required=False, description='Work performed description', example='Checked motor connections'),
    'parts_used': fields.List(fields.Raw, required=False, description='Parts used in service')
})

location_model = api.model('Location', {
    'latitude': fields.Float(required=True, description='Latitude', example=19.0760),
    'longitude': fields.Float(required=True, description='Longitude', example=72.8777)
})

parts_model = api.model('PartsUsed', {
    'parts': fields.List(fields.Raw, required=True, description='List of parts used', example=[
        {'part_id': 1, 'name': 'Motor Belt', 'quantity': 1, 'cost': 250.0},
        {'part_id': 2, 'name': 'Oil Filter', 'quantity': 2, 'cost': 150.0}
    ])
})

# Profile Models
profile_update_model = api.model('ProfileUpdate', {
    'full_name': fields.String(required=False, description='Full name'),
    'phone': fields.String(required=False, description='Phone number'),
    'email': fields.String(required=False, description='Email address'),
    'specializations': fields.List(fields.String, required=False, description='Technical specializations')
})

# Inventory Models
inventory_request_model = api.model('InventoryRequest', {
    'parts': fields.List(fields.Raw, required=True, description='Parts to request', example=[
        {'part_id': 1, 'quantity': 5, 'urgency': 'normal'},
        {'part_id': 2, 'quantity': 2, 'urgency': 'urgent'}
    ]),
    'reason': fields.String(required=False, description='Reason for request', example='Stock running low')
})

# ==================== FALLBACK DATA ====================
FALLBACK_DATA = {
    "technicians": [
        {"id": 1, "employee_id": "EMP001", "full_name": "Test Technician", "email": "test.tech@ostrich.com", "phone": "9876543210", "role": "service_staff", "specializations": ["Motors", "Pumps"], "experience_years": 5},
        {"id": 2, "employee_id": "EMP002", "full_name": "John Technician", "email": "john.tech@ostrich.com", "phone": "9876543220", "role": "service_staff", "specializations": ["Motors", "Pumps"], "experience_years": 5},
        {"id": 3, "employee_id": "EMP003", "full_name": "Jane Tech", "email": "jane.tech@ostrich.com", "phone": "9876543221", "role": "service_staff", "specializations": ["Generators", "Electrical"], "experience_years": 3},
        {"id": 4, "employee_id": "EMP004", "full_name": "Bob Service", "email": "bob.tech@ostrich.com", "phone": "9876543222", "role": "service_staff", "specializations": ["Motors", "Generators"], "experience_years": 7}
    ],
    "tickets": [
        {"id": 1, "ticket_number": "TKT000001", "customer_name": "John Customer", "customer_phone": "9876543210", "customer_address": "123 Main St, Mumbai", "product_name": "3HP Motor", "product_model": "OST-3HP-SP", "issue_description": "Motor not starting properly", "status": "SCHEDULED", "priority": "HIGH", "assigned_technician_id": 1, "scheduled_date": "2025-01-15T09:00:00", "created_at": "2025-01-14T10:00:00"},
        {"id": 2, "ticket_number": "TKT000002", "customer_name": "Jane Smith", "customer_phone": "9876543211", "customer_address": "456 Service Ave, Delhi", "product_name": "5HP Pump", "product_model": "OST-5HP-MP", "issue_description": "Pump maintenance required", "status": "IN_PROGRESS", "priority": "MEDIUM", "assigned_technician_id": 1, "scheduled_date": "2025-01-15T14:00:00", "created_at": "2025-01-13T15:30:00"},
        {"id": 3, "ticket_number": "TKT000003", "customer_name": "Bob Wilson", "customer_phone": "9876543212", "customer_address": "789 Repair Rd, Bangalore", "product_name": "7HP Generator", "product_model": "OST-7HP-GN", "issue_description": "Generator overheating issue", "status": "COMPLETED", "priority": "HIGH", "assigned_technician_id": 2, "scheduled_date": "2025-01-14T11:00:00", "created_at": "2025-01-12T09:15:00", "completed_at": "2025-01-14T16:30:00"}
    ],
    "notifications": [
        {"id": 1, "technician_id": 1, "title": "New Ticket Assigned", "message": "Ticket TKT000004 has been assigned to you", "type": "assignment", "is_read": False, "created_at": "2025-01-15T10:00:00", "ticket_id": 4},
        {"id": 2, "technician_id": 1, "title": "Urgent Ticket", "message": "High priority ticket TKT000005 needs immediate attention", "type": "urgent", "is_read": False, "created_at": "2025-01-15T09:30:00", "ticket_id": 5},
        {"id": 3, "technician_id": 1, "title": "Schedule Update", "message": "Your schedule for tomorrow has been updated", "type": "schedule", "is_read": True, "created_at": "2025-01-14T17:00:00", "ticket_id": None}
    ],
    "inventory": [
        {"id": 1, "part_number": "BRG001", "name": "Motor Bearing", "category": "Bearings", "quantity_available": 15, "unit_cost": 250.0, "location": "Van Inventory"},
        {"id": 2, "part_number": "WND001", "name": "Motor Winding", "category": "Electrical", "quantity_available": 5, "unit_cost": 1500.0, "location": "Warehouse"},
        {"id": 3, "part_number": "FLT001", "name": "Oil Filter", "category": "Filters", "quantity_available": 25, "unit_cost": 75.0, "location": "Van Inventory"},
        {"id": 4, "part_number": "BLT001", "name": "Drive Belt", "category": "Belts", "quantity_available": 10, "unit_cost": 125.0, "location": "Van Inventory"}
    ]
}

# Helper functions - Updated for users table
def get_technician_data(technician_id):
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM users WHERE id = %s AND role = 'service_staff'", (technician_id,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                # Map user fields to technician format
                return {
                    'id': result['id'],
                    'employee_id': f"EMP{result['id']:03d}",
                    'full_name': f"{result.get('first_name', '')} {result.get('last_name', '')}".strip(),
                    'email': result.get('email', ''),
                    'phone': result.get('phone', ''),
                    'role': result.get('role', 'service_staff'),
                    'specializations': ['Motors', 'Pumps'],  # Default for now
                    'experience_years': 5
                }
        # Return None if no database result instead of fallback
        return None

def get_technician_tickets(technician_id, status=None):
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            query = "SELECT st.*, c.contact_person as customer_name, c.phone as customer_phone, c.address as customer_address FROM service_tickets st LEFT JOIN customers c ON st.customer_id = c.id WHERE st.assigned_staff_id = %s"
            params = [technician_id]
            if status:
                query += " AND st.status = %s"
                params.append(status.upper())
            try:
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                if results:
                    # Convert datetime objects to strings for JSON serialization
                    for result in results:
                        for key, value in result.items():
                            if hasattr(value, 'isoformat'):
                                result[key] = value.isoformat()
                    return results
            except Exception as e:
                print(f"Database query error: {e}")
                cursor.close()
    return []  # Return empty list instead of fallback data

def get_technician_notifications(technician_id):
    with get_db_connection() as conn:
        if conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC", (technician_id,))
            results = cursor.fetchall()
            cursor.close()
            if results:
                # Convert datetime objects to strings for JSON serialization
                for result in results:
                    for key, value in result.items():
                        if hasattr(value, 'isoformat'):
                            result[key] = value.isoformat()
                    # Map user_id to technician_id for compatibility
                    result['technician_id'] = result.get('user_id')
                    result['is_read'] = bool(result.get('is_read', False))
                return results
    return []  # Return empty list instead of fallback data



# ==================== AUTHENTICATION ENDPOINTS ====================
@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.doc('technician_login')
    @auth_ns.response(200, 'Login successful')
    @auth_ns.response(401, 'Invalid credentials')
    def post(self):
        """Technician login with username/password"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            print(f"Login attempt: {username}")  # Keep minimal logging
            
            # Check database for real users first
            with get_db_connection() as conn:
                if conn:
                    cursor = conn.cursor(pymysql.cursors.DictCursor)
                    cursor.execute("""
                        SELECT * FROM users 
                        WHERE username = %s AND password_hash = %s AND role = 'service_staff' AND is_active = 1
                    """, (username, password))
                    user = cursor.fetchone()
                    cursor.close()
                    
                    if user:
                        access_token = create_access_token({"sub": str(user['id']), "username": username, "role": user['role']})
                        print(f"Database login successful for: {username}")
                        return {
                            "message": "Login successful",
                            "status": True,
                            "data": {
                                "access_token": access_token,
                                "token_type": "bearer",
                                "technician_id": user['id'],
                                "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                "role": user['role'],
                                "employee_id": f"EMP{user['id']:03d}"
                            }
                        }
                else:
                    print("Database connection failed - cannot authenticate users")
                    return {"message": "Database connection failed", "status": False, "data": None}, 500
            
            print(f"Login failed for: {username}")
            return {"message": "Invalid username or password", "status": False, "data": None}, 401
        
        except Exception as e:
            print(f"Login error: {e}")
            return {"message": "Internal server error", "status": False, "data": None}, 500



@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('technician_logout', security='Bearer')
    @auth_ns.response(200, 'Logout successful')
    @api.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """Technician logout"""
        return {
            "message": "Logout successful",
            "status": True,
            "data": {
                "logged_out_at": datetime.now().isoformat()
            }
        }

@auth_ns.route('/send-otp')
class SendOTP(Resource):
    @auth_ns.expect(otp_model)
    @auth_ns.doc('send_otp')
    @auth_ns.response(200, 'OTP sent successfully')
    def post(self):
        """Send OTP to technician's phone"""
        data = request.get_json()
        contact = data.get('contact')
        otp_code = "123456"  # In production, generate random OTP
        
        print(f"📱 OTP SEND: contact={contact}, otp={otp_code}")
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                # Store OTP in database
                cursor.execute("""
                    INSERT INTO otp_logs (phone_number, otp_code, purpose, status, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    contact, otp_code, 'login', 'sent',
                    datetime.now() + timedelta(minutes=5)
                ))
                conn.commit()
                cursor.close()
                print(f"✅ OTP stored in database for {contact}")
        
        return {
            "message": "OTP sent successfully",
            "status": True,
            "data": {
                "contact": contact,
                "otp": otp_code,  # Remove in production
                "expires_in": "5 minutes"
            }
        }

@auth_ns.route('/verify-otp')
class VerifyOTP(Resource):
    @auth_ns.expect(verify_otp_model)
    @auth_ns.doc('verify_otp')
    @auth_ns.response(200, 'OTP verified successfully')
    @auth_ns.response(400, 'Invalid OTP')
    def post(self):
        """Verify OTP and authenticate"""
        data = request.get_json()
        otp = data.get('otp')
        contact = data.get('contact')
        
        print(f"OTP verification attempt: contact={contact}")
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                # Check OTP in database
                cursor.execute("""
                    SELECT * FROM otp_logs 
                    WHERE phone_number = %s AND otp_code = %s AND status = 'sent' AND expires_at > %s
                    ORDER BY created_at DESC LIMIT 1
                """, (contact, otp, datetime.now()))
                
                otp_record = cursor.fetchone()
                print(f"OTP record found: {otp_record is not None}")
                
                if otp_record:
                    # Mark OTP as verified
                    cursor.execute("""
                        UPDATE otp_logs SET status = 'verified', verified_at = %s WHERE id = %s
                    """, (datetime.now(), otp_record['id']))
                    
                    # Find user by phone
                    cursor.execute("""
                        SELECT * FROM users WHERE phone = %s AND role = 'service_staff' AND is_active = 1
                    """, (contact,))
                    user = cursor.fetchone()
                    print(f"User found: {user is not None}")
                    
                    conn.commit()
                    cursor.close()
                    
                    if user:
                        access_token = create_access_token({"sub": str(user['id']), "phone": contact, "otp_verified": True})
                        return {
                            "message": "OTP verified successfully",
                            "status": True,
                            "data": {
                                "access_token": access_token,
                                "token_type": "bearer",
                                "technician_id": user['id'],
                                "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                                "role": user['role'],
                                "phone": contact
                            }
                        }
                    else:
                        print(f"No user found with phone {contact} and role service_staff")
                        # Fallback to test data for demo
                        test_user = next((t for t in FALLBACK_DATA['technicians'] if t['phone'] == contact), None)
                        if test_user:
                            access_token = create_access_token({"sub": str(test_user['id']), "phone": contact, "otp_verified": True})
                            return {
                                "message": "OTP verified successfully (demo mode)",
                                "status": True,
                                "data": {
                                    "access_token": access_token,
                                    "token_type": "bearer",
                                    "technician_id": test_user['id'],
                                    "full_name": test_user['full_name'],
                                    "role": test_user['role'],
                                    "phone": contact
                                }
                            }
                cursor.close()
            else:
                print("Database connection failed")
                return {"message": "Database connection failed", "status": False, "data": None}, 500
        
        return {"message": "Invalid or expired OTP", "status": False, "data": None}, 400

# ==================== DASHBOARD ENDPOINTS ====================
@dashboard_ns.route('/')
class Dashboard(Resource):
    @dashboard_ns.doc('get_dashboard', security='Bearer')
    @dashboard_ns.response(200, 'Dashboard data retrieved')
    @dashboard_ns.response(401, 'Unauthorized')
    def get(self):
        """Get technician dashboard overview"""
        # Check for authorization header first
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return {'message': 'Token required', 'status': False, 'data': None}, 401
        
        token = token[7:]
        payload = verify_token(token)
        if not payload:
            return {'message': 'Invalid or expired token', 'status': False, 'data': None}, 401
        
        technician_id = int(payload.get('sub', 1))
        technician = get_technician_data(technician_id)
        if not technician:
            return {'message': 'Technician not found', 'status': False, 'data': None}, 404
        
        tickets = get_technician_tickets(technician_id)
        
        return {
            "message": "Dashboard data retrieved successfully",
            "status": True,
            "data": {
                "technician": technician,
                "stats": {
                    "total_tickets": len(tickets),
                    "pending_tickets": len([t for t in tickets if t["status"] == "SCHEDULED"]),
                    "in_progress_tickets": len([t for t in tickets if t["status"] == "IN_PROGRESS"]),
                    "completed_tickets": len([t for t in tickets if t["status"] == "COMPLETED"]),
                    "completed_today": len([t for t in tickets if t["status"] == "COMPLETED" and t.get("completed_at", "").startswith(datetime.now().strftime('%Y-%m-%d'))])
                },
                "recent_tickets": tickets[:5],
                "performance": {
                    "avg_resolution_time": "2.5 hours",
                    "customer_rating": 4.7,
                    "completion_rate": 95.5,
                    "on_time_percentage": 92.3
                }
            }
        }



# ==================== TICKETS ENDPOINTS ====================
@tickets_ns.route('/assigned')
class AssignedTickets(Resource):
    @tickets_ns.doc('get_assigned_tickets', security='Bearer')
    @tickets_ns.param('status', 'Filter by status', enum=['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'])
    @tickets_ns.param('priority', 'Filter by priority', enum=['LOW', 'MEDIUM', 'HIGH', 'URGENT'])
    @tickets_ns.param('limit', 'Number of tickets to return', type=int, default=10)
    @tickets_ns.param('offset', 'Number of tickets to skip', type=int, default=0)
    @token_required
    def get(self, current_user):
        """Get tickets assigned to technician"""
        technician_id = int(current_user.get('sub', 1))
        status = request.args.get('status')
        priority = request.args.get('priority')
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        tickets = get_technician_tickets(technician_id, status)
        
        if priority:
            tickets = [t for t in tickets if t["priority"].lower() == priority.lower()]
        
        total_count = len(tickets)
        tickets = tickets[offset:offset + limit]
        
        return {
            "message": "Assigned tickets retrieved successfully",
            "status": True,
            "data": {
                "tickets": tickets,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
        }

@tickets_ns.route('/completed')
class CompletedTickets(Resource):
    @tickets_ns.doc('get_completed_tickets', security='Bearer')
    @tickets_ns.param('limit', 'Number of tickets to return', type=int, default=10)
    @tickets_ns.param('offset', 'Number of tickets to skip', type=int, default=0)
    @token_required
    def get(self, current_user):
        """Get completed tickets"""
        technician_id = int(current_user.get('sub', 1))
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        tickets = get_technician_tickets(technician_id, 'COMPLETED')
        total_count = len(tickets)
        tickets = tickets[offset:offset + limit]
        
        return {
            "message": "Completed tickets retrieved successfully",
            "status": True,
            "data": {
                "tickets": tickets,
                "total_count": total_count
            }
        }

@tickets_ns.route('/<int:ticket_id>')
class TicketDetail(Resource):
    @tickets_ns.doc('get_ticket_details', security='Bearer')
    @tickets_ns.response(200, 'Ticket details retrieved')
    @tickets_ns.response(404, 'Ticket not found')
    @token_required
    def get(self, ticket_id, current_user):
        """Get detailed ticket information"""
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                cursor.execute("""
                    SELECT st.*, c.contact_person as customer_name, c.phone as customer_phone, c.address as customer_address,
                           c.email as customer_email
                    FROM service_tickets st 
                    LEFT JOIN customers c ON st.customer_id = c.id 
                    WHERE st.id = %s
                """, (ticket_id,))
                ticket = cursor.fetchone()
                
                if ticket:
                    # Get parts used
                    cursor.execute("SELECT * FROM service_ticket_parts WHERE ticket_id = %s", (ticket_id,))
                    parts_used = cursor.fetchall()
                    
                    # Convert datetime objects
                    for key, value in ticket.items():
                        if hasattr(value, 'isoformat'):
                            ticket[key] = value.isoformat()
                    
                    ticket['parts_used'] = parts_used or []
                    ticket['photos'] = ticket.get('photos', []) or []
                    cursor.close()
                    
                    return {
                        "message": "Ticket details retrieved successfully",
                        "status": True,
                        "data": {"ticket": ticket}
                    }
                cursor.close()
        
        return {"message": "Ticket not found", "status": False, "data": None}, 404

@tickets_ns.route('/<int:ticket_id>/status')
class UpdateTicketStatus(Resource):
    @tickets_ns.expect(ticket_status_model)
    @tickets_ns.doc('update_ticket_status', security='Bearer')
    @tickets_ns.response(200, 'Status updated successfully')
    @tickets_ns.response(404, 'Ticket not found')
    @token_required
    def put(self, ticket_id, current_user):
        """Update ticket status and add notes"""
        data = request.get_json()
        status = data.get('status', '').upper()
        notes = data.get('notes', '')
        work_performed = data.get('work_performed', '')
        parts_used = data.get('parts_used', [])
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                update_fields = ["status = %s", "technician_notes = %s", "work_performed = %s"]
                params = [status, notes, work_performed]
                
                if status == 'COMPLETED':
                    update_fields.append("completed_date = %s")
                    params.append(datetime.now())
                
                cursor.execute(f"UPDATE service_tickets SET {', '.join(update_fields)} WHERE id = %s", 
                             params + [ticket_id])
                
                # Add parts used
                if parts_used:
                    for part in parts_used:
                        cursor.execute("""
                            INSERT INTO service_ticket_parts (ticket_id, part_name, quantity, unit_cost)
                            VALUES (%s, %s, %s, %s)
                        """, (ticket_id, part.get('name', ''), part.get('quantity', 1), part.get('cost', 0)))
                
                conn.commit()
                cursor.close()
        
        return {
            "message": "Ticket status updated successfully",
            "status": True,
            "data": {
                "ticket_id": ticket_id,
                "new_status": status,
                "updated_at": datetime.now().isoformat(),
                "notes": notes,
                "work_performed": work_performed,
                "parts_used": parts_used
            }
        }

@tickets_ns.route('/<int:ticket_id>/location')
class CaptureLocation(Resource):
    @tickets_ns.expect(location_model)
    @tickets_ns.doc('capture_location', security='Bearer')
    @tickets_ns.response(200, 'Location captured successfully')
    @token_required
    def post(self, ticket_id, current_user):
        """Capture technician location for ticket"""
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE service_tickets 
                    SET technician_latitude = %s, technician_longitude = %s, location_captured_at = %s
                    WHERE id = %s
                """, (latitude, longitude, datetime.now(), ticket_id))
                conn.commit()
                cursor.close()
        
        return {
            "message": "Location captured successfully",
            "status": True,
            "data": {
                "ticket_id": ticket_id,
                "latitude": latitude,
                "longitude": longitude,
                "captured_at": datetime.now().isoformat()
            }
        }

@tickets_ns.route('/<int:ticket_id>/photos')
class UploadPhotos(Resource):
    @tickets_ns.doc('upload_photos', security='Bearer')
    @tickets_ns.response(200, 'Photos uploaded successfully')
    @token_required
    def post(self, ticket_id, current_user):
        """Upload photos for ticket"""
        import json
        
        # Mock photo URLs for demo
        photo_urls = [
            f"https://example.com/photos/{ticket_id}_1.jpg",
            f"https://example.com/photos/{ticket_id}_2.jpg",
            f"https://example.com/photos/{ticket_id}_3.jpg"
        ]
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE service_tickets 
                    SET photos = %s, photo_count = %s
                    WHERE id = %s
                """, (json.dumps(photo_urls), len(photo_urls), ticket_id))
                conn.commit()
                cursor.close()
        
        return {
            "message": "Photos uploaded successfully",
            "status": True,
            "data": {
                "ticket_id": ticket_id,
                "photo_count": len(photo_urls),
                "photo_urls": photo_urls,
                "uploaded_at": datetime.now().isoformat()
            }
        }

@tickets_ns.route('/<int:ticket_id>/signature')
class CaptureSignature(Resource):
    @tickets_ns.doc('capture_signature', security='Bearer')
    @tickets_ns.response(200, 'Signature captured successfully')
    @token_required
    def post(self, ticket_id, current_user):
        """Capture customer signature"""
        try:
            data = request.get_json(force=True) or {}
        except:
            data = {}
        
        customer_name = data.get('customer_name', 'Customer')
        signature_url = f"https://example.com/signatures/{ticket_id}_signature.png"
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE service_tickets 
                    SET customer_signature_url = %s, signature_captured_at = %s, customer_signature_name = %s
                    WHERE id = %s
                """, (signature_url, datetime.now(), customer_name, ticket_id))
                conn.commit()
                cursor.close()
        
        return {
            "message": "Customer signature captured successfully",
            "status": True,
            "data": {
                "ticket_id": ticket_id,
                "signature_url": signature_url,
                "captured_at": datetime.now().isoformat(),
                "customer_name": customer_name
            }
        }

@tickets_ns.route('/<int:ticket_id>/parts')
class AddPartsUsed(Resource):
    @tickets_ns.expect(parts_model)
    @tickets_ns.doc('add_parts_used', security='Bearer')
    @tickets_ns.response(200, 'Parts information updated')
    @token_required
    def post(self, ticket_id, current_user):
        """Add parts used in service"""
        data = request.get_json()
        parts = data.get('parts', [])
        
        total_cost = sum(part.get('cost', 0) * part.get('quantity', 1) for part in parts)
        
        return {
            "message": "Parts information updated successfully",
            "status": True,
            "data": {
                "ticket_id": ticket_id,
                "parts_added": len(parts),
                "total_cost": total_cost,
                "parts": parts,
                "updated_at": datetime.now().isoformat()
            }
        }

# ==================== NOTIFICATIONS ENDPOINTS ====================
@notifications_ns.route('/')
class Notifications(Resource):
    @notifications_ns.doc('get_notifications', security='Bearer')
    @notifications_ns.param('limit', 'Number of notifications to return', type=int, default=20)
    @notifications_ns.param('unread_only', 'Show only unread notifications', type=bool, default=False)
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get technician notifications"""
        technician_id = int(current_user.get('sub', 1))
        limit = int(request.args.get('limit', 20))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        notifications = get_technician_notifications(technician_id)
        
        if unread_only:
            notifications = [n for n in notifications if not n["is_read"]]
        
        return {
            "message": "Notifications retrieved successfully",
            "status": True,
            "data": {
                "notifications": notifications[:limit],
                "total_count": len(notifications),
                "unread_count": len([n for n in notifications if not n["is_read"]])
            }
        }

@notifications_ns.route('/<int:notification_id>/read')
class MarkNotificationRead(Resource):
    @notifications_ns.doc('mark_notification_read', security='Bearer')
    @notifications_ns.response(200, 'Notification marked as read')
    @api.doc(security='Bearer')
    @token_required
    def put(self, notification_id, current_user):
        """Mark notification as read"""
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s", (notification_id,))
                conn.commit()
                cursor.close()
        
        return {
            "message": f"Notification {notification_id} marked as read",
            "status": True,
            "data": {
                "notification_id": notification_id,
                "marked_at": datetime.now().isoformat()
            }
        }

@notifications_ns.route('/unread-count')
class UnreadCount(Resource):
    @notifications_ns.doc('get_unread_count', security='Bearer')
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get unread notifications count"""
        technician_id = int(current_user.get('sub', 1))
        notifications = get_technician_notifications(technician_id)
        unread_count = len([n for n in notifications if not n["is_read"]])
        
        return {
            "message": "Unread count retrieved successfully",
            "status": True,
            "data": {"unread_count": unread_count}
        }

@notifications_ns.route('/mark-all-read')
class MarkAllRead(Resource):
    @notifications_ns.doc('mark_all_read', security='Bearer')
    @api.doc(security='Bearer')
    @token_required
    def put(self, current_user):
        """Mark all notifications as read"""
        technician_id = int(current_user.get('sub', 1))
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = %s", (technician_id,))
                updated_count = cursor.rowcount
                conn.commit()
                cursor.close()
            else:
                updated_count = 0
        
        return {
            "message": "All notifications marked as read",
            "status": True,
            "data": {
                "technician_id": technician_id,
                "updated_count": updated_count,
                "marked_at": datetime.now().isoformat()
            }
        }

# ==================== SCHEDULE ENDPOINTS ====================
@schedule_ns.route('/')
class Schedule(Resource):
    @schedule_ns.doc('get_schedule', security='Bearer')
    @schedule_ns.param('date', 'Date in YYYY-MM-DD format', default=datetime.now().strftime('%Y-%m-%d'))
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get technician schedule for specific date"""
        technician_id = int(current_user.get('sub', 1))
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        tickets = get_technician_tickets(technician_id, 'SCHEDULED')
        scheduled_tickets = [t for t in tickets if t["scheduled_date"].startswith(date)]
        
        return {
            "message": "Schedule retrieved successfully",
            "status": True,
            "data": {
                "date": date,
                "appointments": [
                    {
                        "id": ticket["id"],
                        "ticket_number": ticket["ticket_number"],
                        "customer_name": ticket["customer_name"],
                        "start_time": ticket["scheduled_date"].split('T')[1][:5] if 'T' in ticket["scheduled_date"] else "09:00",
                        "end_time": "11:00",  # Estimated
                        "status": ticket["status"],
                        "address": ticket["customer_address"],
                        "priority": ticket["priority"],
                        "product_name": ticket["product_name"]
                    } for ticket in scheduled_tickets
                ],
                "total_appointments": len(scheduled_tickets),
                "working_hours": {"start": "08:00", "end": "18:00"}
            }
        }

@schedule_ns.route('/week')
class WeeklySchedule(Resource):
    @schedule_ns.doc('get_weekly_schedule', security='Bearer')
    @schedule_ns.param('week_start', 'Week start date in YYYY-MM-DD format')
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get technician weekly schedule"""
        technician_id = int(current_user.get('sub', 1))
        tickets = get_technician_tickets(technician_id)
        
        # Group tickets by date
        weekly_schedule = {}
        for i in range(7):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            day_tickets = [t for t in tickets if t["scheduled_date"].startswith(date)]
            weekly_schedule[date] = {
                "date": date,
                "day_name": (datetime.now() + timedelta(days=i)).strftime('%A'),
                "appointments": len(day_tickets),
                "tickets": day_tickets
            }
        
        return {
            "message": "Weekly schedule retrieved successfully",
            "status": True,
            "data": {"weekly_schedule": weekly_schedule}
        }

# ==================== PROFILE ENDPOINTS ====================
@profile_ns.route('/')
class Profile(Resource):
    @profile_ns.doc('get_profile', security='Bearer')
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get technician profile"""
        technician_id = int(current_user.get('sub', 1))
        technician = get_technician_data(technician_id)
        tickets = get_technician_tickets(technician_id)
        
        profile_data = technician.copy()
        profile_data.update({
            "department": "Field Service",
            "join_date": "2020-01-15",
            "performance_rating": 4.8,
            "completed_tickets_total": len([t for t in tickets if t["status"] == "COMPLETED"]),
            "certification_level": "Senior Technician",
            "last_login": datetime.now().isoformat()
        })
        
        return {
            "message": "Profile retrieved successfully",
            "status": True,
            "data": profile_data
        }
    
    @profile_ns.expect(profile_update_model)
    @profile_ns.doc('update_profile', security='Bearer')
    @api.doc(security='Bearer')
    @token_required
    def put(self, current_user):
        """Update technician profile"""
        data = request.get_json()
        technician_id = int(current_user.get('sub', 1))
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                update_fields = []
                params = []
                
                if 'full_name' in data:
                    names = data['full_name'].split(' ', 1)
                    update_fields.extend(["first_name = %s", "last_name = %s"])
                    params.extend([names[0], names[1] if len(names) > 1 else ''])
                
                if 'phone' in data:
                    update_fields.append("phone = %s")
                    params.append(data['phone'])
                
                if 'email' in data:
                    update_fields.append("email = %s")
                    params.append(data['email'])
                
                if update_fields:
                    cursor.execute(f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s", 
                                 params + [technician_id])
                    conn.commit()
                
                cursor.close()
        
        return {
            "message": "Profile updated successfully",
            "status": True,
            "data": {
                "updated_fields": list(data.keys()),
                "updated_at": datetime.now().isoformat()
            }
        }

# ==================== REPORTS ENDPOINTS ====================
# Reports endpoints removed - not needed for core service functionality

# ==================== INVENTORY ENDPOINTS ====================
@inventory_ns.route('/parts')
class InventoryParts(Resource):
    @inventory_ns.doc('get_inventory_parts', security='Bearer')
    @inventory_ns.param('category', 'Filter by category')
    @inventory_ns.param('location', 'Filter by location', enum=['Van Inventory', 'Warehouse'])
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get available parts inventory"""
        category = request.args.get('category')
        location = request.args.get('location')
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                query = "SELECT * FROM inventory WHERE 1=1"
                params = []
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                if location:
                    query += " AND location = %s"
                    params.append(location)
                
                cursor.execute(query, params)
                parts = cursor.fetchall()
                
                # Get categories and locations
                cursor.execute("SELECT DISTINCT category FROM inventory")
                categories = [row['category'] for row in cursor.fetchall()]
                
                cursor.execute("SELECT DISTINCT location FROM inventory")
                locations = [row['location'] for row in cursor.fetchall()]
                
                cursor.close()
                
                return {
                    "message": "Inventory parts retrieved successfully",
                    "status": True,
                    "data": {
                        "parts": parts,
                        "total_count": len(parts),
                        "categories": categories,
                        "locations": locations
                    }
                }
        
        return {
            "message": "No inventory data available",
            "status": False,
            "data": {"parts": [], "total_count": 0, "categories": [], "locations": []}
        }

@inventory_ns.route('/request')
class InventoryRequest(Resource):
    @inventory_ns.expect(inventory_request_model)
    @inventory_ns.doc('request_parts', security='Bearer')
    @inventory_ns.response(201, 'Parts request submitted')
    @api.doc(security='Bearer')
    @token_required
    def post(self, current_user):
        """Request parts from inventory"""
        import json
        data = request.get_json()
        parts = data.get('parts', [])
        reason = data.get('reason', '')
        technician_id = int(current_user.get('sub', 1))
        request_id = f"REQ{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO parts_requests (request_id, technician_id, status, reason, parts_requested, parts_count, estimated_delivery)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    request_id, technician_id, 'pending_approval', reason,
                    json.dumps(parts), len(parts), 
                    (datetime.now() + timedelta(days=2)).date()
                ))
                conn.commit()
                cursor.close()
        
        return {
            "message": "Parts request submitted successfully",
            "status": True,
            "data": {
                "request_id": request_id,
                "technician_id": technician_id,
                "parts_requested": len(parts),
                "estimated_delivery": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
                "status": "pending_approval",
                "reason": reason,
                "submitted_at": datetime.now().isoformat()
            }
        }, 201

@inventory_ns.route('/requests')
class InventoryRequests(Resource):
    @inventory_ns.doc('get_inventory_requests', security='Bearer')
    @inventory_ns.param('status', 'Filter by status', enum=['pending_approval', 'approved', 'delivered', 'cancelled'])
    @api.doc(security='Bearer')
    @token_required
    def get(self, current_user):
        """Get technician's parts requests"""
        technician_id = int(current_user.get('sub', 1))
        status = request.args.get('status')
        
        with get_db_connection() as conn:
            if conn:
                cursor = conn.cursor(pymysql.cursors.DictCursor)
                query = "SELECT * FROM parts_requests WHERE technician_id = %s"
                params = [technician_id]
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC"
                cursor.execute(query, params)
                requests = cursor.fetchall()
                
                # Convert datetime objects
                for req in requests:
                    for key, value in req.items():
                        if hasattr(value, 'isoformat'):
                            req[key] = value.isoformat()
                
                cursor.close()
                
                return {
                    "message": "Inventory requests retrieved successfully",
                    "status": True,
                    "data": {
                        "requests": requests,
                        "total_count": len(requests)
                    }
                }
        
        return {
            "message": "No inventory requests found",
            "status": True,
            "data": {"requests": [], "total_count": 0}
        }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8002))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    print(f"Starting Ostrich Service Technician API on port {port}")
    print(f"Swagger UI available at: http://0.0.0.0:{port}/docs/")
    print(f"Test credentials: username='demo.tech', password='password123'")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
