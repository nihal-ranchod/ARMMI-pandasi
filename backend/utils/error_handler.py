import logging
import traceback
from functools import wraps
from flask import jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge, BadRequest, NotFound
from .security import security_manager

logger = logging.getLogger(__name__)

class PharmaQueryError(Exception):
    """Base exception for PharmaQuery application"""
    def __init__(self, message, status_code=500, error_type="GENERAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        super().__init__(self.message)

class ValidationError(PharmaQueryError):
    """Validation error exception"""
    def __init__(self, message):
        super().__init__(message, 400, "VALIDATION_ERROR")

class SecurityError(PharmaQueryError):
    """Security-related error exception"""
    def __init__(self, message):
        super().__init__(message, 403, "SECURITY_ERROR")

class DataProcessingError(PharmaQueryError):
    """Data processing error exception"""
    def __init__(self, message):
        super().__init__(message, 422, "DATA_PROCESSING_ERROR")

class QueryExecutionError(PharmaQueryError):
    """Query execution error exception"""
    def __init__(self, message):
        super().__init__(message, 500, "QUERY_EXECUTION_ERROR")

class ErrorHandler:
    """Centralized error handling for the application"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handlers for Flask app"""
        
        @app.errorhandler(PharmaQueryError)
        def handle_pharmaquery_error(error):
            logger.error(f"PharmaQuery Error: {error.error_type} - {error.message}")
            return self._create_error_response(
                error.message,
                error.status_code,
                error.error_type
            )
        
        @app.errorhandler(ValidationError)
        def handle_validation_error(error):
            logger.warning(f"Validation Error: {error.message}")
            return self._create_error_response(error.message, 400, "VALIDATION_ERROR")
        
        @app.errorhandler(SecurityError)
        def handle_security_error(error):
            logger.error(f"Security Error: {error.message} - IP: {request.remote_addr}")
            return self._create_error_response(
                "Access denied due to security policy",
                403,
                "SECURITY_ERROR"
            )
        
        @app.errorhandler(DataProcessingError)
        def handle_data_processing_error(error):
            logger.error(f"Data Processing Error: {error.message}")
            return self._create_error_response(error.message, 422, "DATA_PROCESSING_ERROR")
        
        @app.errorhandler(QueryExecutionError)
        def handle_query_execution_error(error):
            logger.error(f"Query Execution Error: {error.message}")
            return self._create_error_response(error.message, 500, "QUERY_EXECUTION_ERROR")
        
        @app.errorhandler(RequestEntityTooLarge)
        def handle_file_too_large(error):
            logger.warning(f"File too large error - IP: {request.remote_addr}")
            return self._create_error_response(
                "File too large. Maximum size: 100MB",
                413,
                "FILE_TOO_LARGE"
            )
        
        @app.errorhandler(BadRequest)
        def handle_bad_request(error):
            logger.warning(f"Bad Request: {error.description} - IP: {request.remote_addr}")
            return self._create_error_response(
                "Invalid request format",
                400,
                "BAD_REQUEST"
            )
        
        @app.errorhandler(NotFound)
        def handle_not_found(error):
            logger.info(f"404 Not Found: {request.url} - IP: {request.remote_addr}")
            return self._create_error_response(
                "Resource not found",
                404,
                "NOT_FOUND"
            )
        
        @app.errorhandler(500)
        def handle_internal_server_error(error):
            logger.error(f"Internal Server Error: {str(error)}")
            logger.error(traceback.format_exc())
            return self._create_error_response(
                "Internal server error occurred",
                500,
                "INTERNAL_ERROR"
            )
        
        @app.errorhandler(Exception)
        def handle_unexpected_error(error):
            logger.error(f"Unexpected Error: {str(error)}")
            logger.error(traceback.format_exc())
            
            # Sanitize error message
            sanitized_message = security_manager.sanitize_error_message(str(error))
            
            return self._create_error_response(
                f"An unexpected error occurred: {sanitized_message}",
                500,
                "UNEXPECTED_ERROR"
            )
    
    def _create_error_response(self, message, status_code, error_type):
        """Create standardized error response"""
        return jsonify({
            'success': False,
            'error': message,
            'error_type': error_type,
            'status_code': status_code
        }), status_code

def handle_exceptions(f):
    """Decorator for handling exceptions in route functions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError:
            raise  # Re-raise to be caught by error handlers
        except SecurityError:
            raise  # Re-raise to be caught by error handlers
        except DataProcessingError:
            raise  # Re-raise to be caught by error handlers
        except QueryExecutionError:
            raise  # Re-raise to be caught by error handlers
        except Exception as e:
            logger.error(f"Unhandled exception in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Convert to PharmaQueryError for consistent handling
            sanitized_message = security_manager.sanitize_error_message(str(e))
            raise PharmaQueryError(f"Operation failed: {sanitized_message}")
    
    return decorated_function

def validate_json_input(required_fields=None, optional_fields=None):
    """Decorator for validating JSON input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                raise ValidationError("Request must contain valid JSON")
            
            data = request.get_json()
            if data is None:
                raise ValidationError("Invalid JSON data")
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate field types if specified
            for field, expected_type in (required_fields or {}).items():
                if field in data and not isinstance(data[field], expected_type):
                    raise ValidationError(f"Field '{field}' must be of type {expected_type.__name__}")
            
            for field, expected_type in (optional_fields or {}).items():
                if field in data and not isinstance(data[field], expected_type):
                    raise ValidationError(f"Field '{field}' must be of type {expected_type.__name__}")
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

class RequestLogger:
    """Request logging utility"""
    
    @staticmethod
    def log_request():
        """Log incoming request details"""
        logger.info(
            f"REQUEST: {request.method} {request.path} - "
            f"IP: {request.remote_addr} - "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
        )
    
    @staticmethod
    def log_response(response_data, status_code):
        """Log response details"""
        success = response_data.get('success', False) if isinstance(response_data, dict) else True
        logger.info(
            f"RESPONSE: {status_code} - "
            f"Success: {success} - "
            f"IP: {request.remote_addr}"
        )

def log_requests(f):
    """Decorator for logging requests and responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        RequestLogger.log_request()
        
        try:
            result = f(*args, **kwargs)
            
            # Extract status code and data from Flask response
            if isinstance(result, tuple):
                response_data, status_code = result[0], result[1]
            else:
                response_data, status_code = result, 200
            
            RequestLogger.log_response(response_data, status_code)
            return result
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)} - IP: {request.remote_addr}")
            raise
    
    return decorated_function

# Utility functions for common validations
def validate_dataset_id(dataset_id):
    """Validate dataset ID format"""
    if not dataset_id:
        raise ValidationError("Dataset ID is required")
    
    if not isinstance(dataset_id, str):
        raise ValidationError("Dataset ID must be a string")
    
    if len(dataset_id) < 10 or len(dataset_id) > 50:
        raise ValidationError("Dataset ID has invalid format")
    
    return True

def validate_query_text(query_text):
    """Validate query text"""
    validation_result = security_manager.validate_query_text(query_text)
    if not validation_result['valid']:
        raise ValidationError(validation_result['error'])
    
    return True

def validate_file_upload(file):
    """Validate file upload"""
    if not file:
        raise ValidationError("No file provided")
    
    if not file.filename:
        raise ValidationError("File has no name")
    
    # Additional file validations can be added here
    return True