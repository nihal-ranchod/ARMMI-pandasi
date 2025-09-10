import os
import hashlib
import secrets
import re
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security utilities for PharmaQuery application"""
    
    def __init__(self):
        self.max_query_length = 10000
        self.max_filename_length = 255
        self.blocked_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'eval\(',
            r'exec\(',
        ]
    
    def sanitize_filename(self, filename):
        """Sanitize filename for safe storage"""
        if not filename:
            return None
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Limit length
        if len(filename) > self.max_filename_length:
            name, ext = os.path.splitext(filename)
            max_name_length = self.max_filename_length - len(ext) - 1
            filename = name[:max_name_length] + ext
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Ensure it's not empty
        if not filename.strip():
            filename = f"file_{secrets.token_hex(8)}.dat"
        
        return filename
    
    def validate_query_text(self, query_text):
        """Validate query text for security issues"""
        if not query_text:
            return {"valid": False, "error": "Query text is empty"}
        
        # Check length
        if len(query_text) > self.max_query_length:
            return {
                "valid": False, 
                "error": f"Query too long. Maximum length: {self.max_query_length} characters"
            }
        
        # Check for suspicious patterns
        query_lower = query_text.lower()
        for pattern in self.blocked_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE | re.DOTALL):
                logger.warning(f"Blocked potentially malicious query pattern: {pattern}")
                return {
                    "valid": False, 
                    "error": "Query contains potentially unsafe content"
                }
        
        return {"valid": True}
    
    def generate_secure_id(self, length=32):
        """Generate a cryptographically secure random ID"""
        return secrets.token_urlsafe(length)
    
    def hash_content(self, content):
        """Generate SHA-256 hash of content for integrity checking"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    def validate_api_key(self, api_key):
        """Validate OpenAI API key format"""
        if not api_key:
            return False
        
        # Basic format validation for OpenAI API keys
        if not api_key.startswith('sk-'):
            return False
        
        # Check length (OpenAI keys are typically longer than 40 chars)
        if len(api_key) < 40:
            return False
        
        return True
    
    def sanitize_error_message(self, error_message):
        """Sanitize error messages to prevent information leakage"""
        # Don't expose file paths
        error_message = re.sub(r'/[^\s]+', '[PATH]', str(error_message))
        
        # Don't expose API keys
        error_message = re.sub(r'sk-[a-zA-Z0-9]+', '[API_KEY]', error_message)
        
        # Limit error message length
        if len(error_message) > 200:
            error_message = error_message[:200] + "..."
        
        return error_message

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
        self.max_requests_per_minute = 60
        self.max_upload_requests_per_hour = 10
    
    def is_allowed(self, client_id, request_type="general"):
        """Check if request is allowed based on rate limits"""
        import time
        
        current_time = int(time.time())
        
        if client_id not in self.requests:
            self.requests[client_id] = {}
        
        if request_type not in self.requests[client_id]:
            self.requests[client_id][request_type] = []
        
        # Clean old requests
        if request_type == "upload":
            # Hour-based limit for uploads
            cutoff_time = current_time - 3600
            limit = self.max_upload_requests_per_hour
        else:
            # Minute-based limit for general requests
            cutoff_time = current_time - 60
            limit = self.max_requests_per_minute
        
        self.requests[client_id][request_type] = [
            req_time for req_time in self.requests[client_id][request_type]
            if req_time > cutoff_time
        ]
        
        # Check limit
        if len(self.requests[client_id][request_type]) >= limit:
            return False
        
        # Add current request
        self.requests[client_id][request_type].append(current_time)
        return True

def require_api_key(f):
    """Decorator to require valid OpenAI API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv('OPENAI_API_KEY')
        security_manager = SecurityManager()
        
        if not security_manager.validate_api_key(api_key):
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not configured or invalid'
            }), 500
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(request_type="general"):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rate_limiter = getattr(decorated_function, '_rate_limiter', None)
            if rate_limiter is None:
                rate_limiter = RateLimiter()
                decorated_function._rate_limiter = rate_limiter
            
            # Use IP address as client identifier
            client_id = request.remote_addr or 'unknown'
            
            if not rate_limiter.is_allowed(client_id, request_type):
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please try again later.'
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_content_type(allowed_types):
    """Decorator to validate request content type"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_type = request.content_type or ''
            
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return jsonify({
                    'success': False,
                    'error': f'Invalid content type. Allowed: {", ".join(allowed_types)}'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def log_security_event(event_type, details, severity="INFO"):
    """Log security-related events"""
    logger.log(
        getattr(logging, severity),
        f"SECURITY_EVENT: {event_type} - {details} - IP: {request.remote_addr if request else 'N/A'}"
    )

# Global security manager instance
security_manager = SecurityManager()