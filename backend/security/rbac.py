"""
Role-Based Access Control (RBAC) System
Defines roles, permissions, and authorization middleware
"""

import os
import jwt
import logging
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-CHANGE-IN-PRODUCTION')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

# Role Definitions
class Role:
    """Role enumeration with hierarchy"""
    READER = "reader"
    ANALYST = "analyst"
    ADMIN = "admin"
    SYSTEM = "system"
    
    ALL_ROLES = {READER, ANALYST, ADMIN, SYSTEM}
    
    # Role hierarchy (higher roles inherit lower role permissions)
    HIERARCHY = {
        SYSTEM: {SYSTEM, ADMIN, ANALYST, READER},
        ADMIN: {ADMIN, ANALYST, READER},
        ANALYST: {ANALYST, READER},
        READER: {READER}
    }
    
    @classmethod
    def get_effective_roles(cls, role: str) -> Set[str]:
        """Get all roles a given role can act as (including itself)"""
        return cls.HIERARCHY.get(role, {role})
    
    @classmethod
    def has_permission(cls, user_role: str, required_role: str) -> bool:
        """Check if user_role has permissions of required_role"""
        return required_role in cls.get_effective_roles(user_role)


# Permission Definitions per Role
PERMISSIONS = {
    Role.READER: {
        "view_metadata": True,
        "view_anonymized_results": True,
        "view_analysis": False,
        "view_redacted_text": False,
        "decrypt_fields": False,
        "manage_roles": False,
        "view_audit_logs": False,
        "request_access": True
    },
    Role.ANALYST: {
        "view_metadata": True,
        "view_anonymized_results": True,
        "view_analysis": True,
        "view_redacted_text": True,
        "decrypt_fields": False,
        "manage_roles": False,
        "view_audit_logs": False,
        "request_access": True
    },
    Role.ADMIN: {
        "view_metadata": True,
        "view_anonymized_results": True,
        "view_analysis": True,
        "view_redacted_text": True,
        "decrypt_fields": True,
        "manage_roles": True,
        "view_audit_logs": True,
        "request_access": False,  # Admins don't need to request
        "approve_access": True,
        "manage_encryption": True
    },
    Role.SYSTEM: {
        "view_metadata": True,
        "view_anonymized_results": True,
        "view_analysis": True,
        "view_redacted_text": True,
        "decrypt_fields": True,
        "manage_roles": True,
        "view_audit_logs": True,
        "background_jobs": True,
        "system_operations": True
    }
}


def check_permission(user_roles: List[str], permission: str) -> bool:
    """Check if user has a specific permission"""
    for role in user_roles:
        if role in PERMISSIONS:
            if PERMISSIONS[role].get(permission, False):
                return True
    return False


def get_allowed_fields_for_role(role: str) -> Set[str]:
    """Get fields a role is allowed to access"""
    field_permissions = {
        Role.READER: {
            "id", "user_id", "consent_id", "timestamp", "created_at",
            "anonymized_answer", "score", "feedback", "status"
        },
        Role.ANALYST: {
            "id", "user_id", "consent_id", "timestamp", "created_at",
            "anonymized_answer", "redacted_text", "tokens", "analysis",
            "score", "feedback", "facial_analysis", "status"
        },
        Role.ADMIN: {
            "*"  # All fields including encrypted
        },
        Role.SYSTEM: {
            "*"  # All fields
        }
    }
    
    return field_permissions.get(role, set())


def generate_jwt_token(user_id: str, roles: List[str], scopes: Optional[List[str]] = None) -> str:
    """
    Generate JWT token with roles and scopes
    
    Args:
        user_id: User identifier
        roles: List of user roles
        scopes: Optional list of scopes (API permissions)
    
    Returns:
        JWT token string
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "roles": roles,
        "scopes": scopes or [],
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iss": "ai-interview-bot",
        "type": "access"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Verify and decode JWT token
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check expiration
        if payload.get('exp') and datetime.fromtimestamp(payload['exp']) < datetime.utcnow():
            logger.warning("Token expired")
            return None
        
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def extract_token_from_request() -> Optional[str]:
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization', '')
    
    if auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    return None


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user from request context"""
    return getattr(g, 'current_user', None)


def require_auth(required_roles: Optional[List[str]] = None):
    """
    Decorator to require authentication
    
    Args:
        required_roles: List of roles that can access this endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token
            token = extract_token_from_request()
            
            if not token:
                return jsonify({"error": "No authentication token provided"}), 401
            
            # Verify token
            payload = verify_jwt_token(token)
            
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401
            
            # Store user in request context
            g.current_user = {
                "user_id": payload.get('sub'),
                "roles": payload.get('roles', []),
                "scopes": payload.get('scopes', [])
            }
            
            # Check role permissions
            if required_roles:
                user_roles = g.current_user['roles']
                has_required_role = False
                
                for user_role in user_roles:
                    for required_role in required_roles:
                        if Role.has_permission(user_role, required_role):
                            has_required_role = True
                            break
                    if has_required_role:
                        break
                
                if not has_required_role:
                    logger.warning(f"User {g.current_user['user_id']} attempted to access {request.path} without required roles: {required_roles}")
                    return jsonify({
                        "error": "Insufficient permissions",
                        "required_roles": required_roles,
                        "your_roles": user_roles
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_permission(permission: str):
    """
    Decorator to require specific permission
    
    Args:
        permission: Permission name (e.g., 'decrypt_fields')
    """
    def decorator(f):
        @wraps(f)
        @require_auth()
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            
            user_roles = user.get('roles', [])
            
            if not check_permission(user_roles, permission):
                logger.warning(f"User {user['user_id']} lacks permission '{permission}' for {request.path}")
                return jsonify({
                    "error": f"Permission denied: {permission}",
                    "your_roles": user_roles
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def filter_response_by_role(data: Dict, user_roles: List[str]) -> Dict:
    """
    Filter response data based on user roles
    
    Removes fields user is not allowed to see
    """
    # Find highest role
    highest_role = Role.READER
    for role in user_roles:
        if role == Role.SYSTEM:
            highest_role = Role.SYSTEM
            break
        elif role == Role.ADMIN:
            highest_role = Role.ADMIN
        elif role == Role.ANALYST and highest_role == Role.READER:
            highest_role = Role.ANALYST
    
    allowed_fields = get_allowed_fields_for_role(highest_role)
    
    # If admin/system, return everything
    if "*" in allowed_fields:
        return data
    
    # Filter fields
    filtered = {}
    for key, value in data.items():
        if key in allowed_fields or key.startswith('_'):  # Allow metadata fields
            filtered[key] = value
        else:
            # Mark as redacted
            filtered[key] = "[REDACTED - Insufficient permissions]"
    
    return filtered


def create_service_token(service_name: str, roles: Optional[List[str]] = None) -> str:
    """
    Create a service account token for background jobs
    
    Args:
        service_name: Name of the service
        roles: Roles to assign (defaults to [SYSTEM])
    
    Returns:
        JWT token
    """
    if roles is None:
        roles = [Role.SYSTEM]
    
    service_id = f"service:{service_name}"
    return generate_jwt_token(service_id, roles, scopes=["background_jobs", "system_operations"])


# Development/Testing helpers
def create_dev_admin_token(user_id: str = "dev_admin") -> str:
    """Create admin token for development (DO NOT USE IN PRODUCTION)"""
    logger.warning("🔓 Creating DEV admin token - FOR DEVELOPMENT ONLY!")
    return generate_jwt_token(user_id, [Role.ADMIN], scopes=["*"])


def create_dev_analyst_token(user_id: str = "dev_analyst") -> str:
    """Create analyst token for development"""
    return generate_jwt_token(user_id, [Role.ANALYST])


def create_dev_reader_token(user_id: str = "dev_reader") -> str:
    """Create reader token for development"""
    return generate_jwt_token(user_id, [Role.READER])
