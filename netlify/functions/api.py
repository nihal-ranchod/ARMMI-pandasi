import json
import os
import sys
import tempfile
import uuid
import pandas as pd
from datetime import datetime
import base64
from urllib.parse import parse_qs
import logging

# Add the backend modules to the Python path
sys.path.append('/opt/build/repo/backend')

try:
    from services.data_processor import DataProcessor
    from services.query_engine import QueryEngine
    from utils.file_validator import FileValidator
except ImportError:
    # Fallback for local development
    import importlib.util
    
    # Load modules dynamically
    backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
    
    spec = importlib.util.spec_from_file_location("data_processor", 
                                                 os.path.join(backend_path, 'services', 'data_processor.py'))
    data_processor_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_processor_module)
    
    spec = importlib.util.spec_from_file_location("query_engine", 
                                                 os.path.join(backend_path, 'services', 'query_engine.py'))
    query_engine_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(query_engine_module)
    
    spec = importlib.util.spec_from_file_location("file_validator", 
                                                 os.path.join(backend_path, 'utils', 'file_validator.py'))
    file_validator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(file_validator_module)
    
    DataProcessor = data_processor_module.DataProcessor
    QueryEngine = query_engine_module.QueryEngine
    FileValidator = file_validator_module.FileValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
upload_folder = tempfile.gettempdir()
data_processor = DataProcessor(upload_folder)
query_engine = QueryEngine()
file_validator = FileValidator()

def cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
    }

def json_response(data, status_code=200):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            **cors_headers()
        },
        'body': json.dumps(data, default=str)
    }

def error_response(message, status_code=500):
    return json_response({'success': False, 'error': message}, status_code)

def success_response(data):
    return json_response({'success': True, **data})

def parse_multipart_form_data(body, content_type):
    """Parse multipart form data (simplified)"""
    try:
        # This is a simplified parser - in production, use a proper library
        boundary = content_type.split('boundary=')[1]
        parts = body.split(f'--{boundary}'.encode())
        
        files = {}
        fields = {}
        
        for part in parts:
            if b'Content-Disposition' in part:
                if b'filename=' in part:
                    # File upload
                    headers_end = part.find(b'\r\n\r\n')
                    if headers_end != -1:
                        headers = part[:headers_end].decode()
                        file_data = part[headers_end + 4:]
                        
                        # Extract filename
                        filename_start = headers.find('filename="') + 10
                        filename_end = headers.find('"', filename_start)
                        filename = headers[filename_start:filename_end]
                        
                        # Create a file-like object
                        class FileUpload:
                            def __init__(self, data, filename):
                                self.data = data
                                self.filename = filename
                                self.position = 0
                            
                            def read(self, size=-1):
                                if size == -1:
                                    result = self.data[self.position:]
                                    self.position = len(self.data)
                                else:
                                    result = self.data[self.position:self.position + size]
                                    self.position += size
                                return result
                            
                            def seek(self, position, whence=0):
                                if whence == 0:  # SEEK_SET
                                    self.position = position
                                elif whence == 1:  # SEEK_CUR
                                    self.position += position
                                elif whence == 2:  # SEEK_END
                                    self.position = len(self.data) + position
                            
                            def tell(self):
                                return self.position
                            
                            def save(self, filepath):
                                with open(filepath, 'wb') as f:
                                    f.write(self.data)
                        
                        files['file'] = FileUpload(file_data, filename)
                
        return fields, files
        
    except Exception as e:
        logger.error(f"Error parsing multipart data: {str(e)}")
        return {}, {}

def handler(event, context):
    try:
        method = event['httpMethod']
        path = event['path']
        
        # Handle preflight OPTIONS requests
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers(),
                'body': ''
            }
        
        # Parse path to get endpoint
        path_parts = path.strip('/').split('/')
        if path_parts[0] == '.netlify' and path_parts[1] == 'functions':
            path_parts = path_parts[3:]  # Remove .netlify/functions/api
        
        endpoint = '/' + '/'.join(path_parts) if path_parts else '/'
        
        # Route requests
        if endpoint == '/datasets' and method == 'GET':
            return handle_get_datasets()
        
        elif endpoint == '/upload' and method == 'POST':
            return handle_upload(event)
        
        elif endpoint.startswith('/datasets/') and endpoint.endswith('/preview') and method == 'GET':
            dataset_id = endpoint.split('/')[2]
            return handle_dataset_preview(dataset_id)
        
        elif endpoint.startswith('/datasets/') and endpoint.endswith('/stats') and method == 'GET':
            dataset_id = endpoint.split('/')[2]
            return handle_dataset_stats(dataset_id)
        
        elif endpoint.startswith('/datasets/') and endpoint.endswith('/rename') and method == 'PUT':
            dataset_id = endpoint.split('/')[2]
            return handle_rename_dataset(dataset_id, event)
        
        elif endpoint.startswith('/datasets/') and method == 'DELETE':
            dataset_id = endpoint.split('/')[2]
            return handle_delete_dataset(dataset_id)
        
        elif endpoint == '/query' and method == 'POST':
            return handle_query(event)
        
        elif endpoint == '/query-history' and method == 'GET':
            return handle_query_history()
        
        elif endpoint.startswith('/export/') and method == 'GET':
            result_id = endpoint.split('/')[2]
            return handle_export(result_id, event)
        
        else:
            return error_response('Endpoint not found', 404)
            
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return error_response(str(e))

def handle_get_datasets():
    try:
        datasets = data_processor.list_datasets()
        return success_response({'datasets': datasets})
    except Exception as e:
        logger.error(f"Get datasets error: {str(e)}")
        return error_response(str(e))

def handle_upload(event):
    try:
        content_type = event['headers'].get('content-type', '')
        
        if 'multipart/form-data' not in content_type:
            return error_response('Content type must be multipart/form-data', 400)
        
        # Decode base64 body
        body = base64.b64decode(event['body'])
        
        fields, files = parse_multipart_form_data(body, content_type)
        
        if 'file' not in files:
            return error_response('No file uploaded', 400)
        
        file = files['file']
        
        # Validate file
        validation_result = file_validator.validate_file(file)
        if not validation_result['valid']:
            return error_response(validation_result['error'], 400)
        
        # Process and save file
        dataset_info = data_processor.save_dataset(file)
        return success_response({'dataset': dataset_info})
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return error_response(str(e))

def handle_dataset_preview(dataset_id):
    try:
        preview_data = data_processor.get_dataset_preview(dataset_id)
        return success_response({'preview': preview_data})
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return error_response(str(e))

def handle_dataset_stats(dataset_id):
    try:
        stats = data_processor.get_dataset_stats(dataset_id)
        return success_response({'stats': stats})
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return error_response(str(e))

def handle_rename_dataset(dataset_id, event):
    try:
        body = json.loads(event['body'])
        new_name = body.get('name', '').strip()
        
        if not new_name:
            return error_response('New name is required', 400)
        
        success = data_processor.rename_dataset(dataset_id, new_name)
        if success:
            return success_response({})
        else:
            return error_response('Dataset not found', 404)
    except Exception as e:
        logger.error(f"Rename error: {str(e)}")
        return error_response(str(e))

def handle_delete_dataset(dataset_id):
    try:
        success = data_processor.delete_dataset(dataset_id)
        if success:
            return success_response({})
        else:
            return error_response('Dataset not found', 404)
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        return error_response(str(e))

def handle_query(event):
    try:
        body = json.loads(event['body'])
        query_text = body.get('query', '')
        dataset_ids = body.get('datasets', [])
        
        if not query_text:
            return error_response('Query text is required', 400)
        
        if not dataset_ids:
            return error_response('At least one dataset must be selected', 400)
        
        # Execute query
        result = query_engine.execute_query(query_text, dataset_ids, data_processor)
        return success_response({'result': result})
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return error_response(str(e))

def handle_query_history():
    try:
        history = query_engine.get_query_history()
        return success_response({'history': history})
    except Exception as e:
        logger.error(f"History error: {str(e)}")
        return error_response(str(e))

def handle_export(result_id, event):
    try:
        query_params = parse_qs(event.get('queryStringParameters', {}) or {})
        export_format = query_params.get('format', ['csv'])[0]
        
        file_path = query_engine.export_result(result_id, export_format)
        
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename=query_results_{result_id}.{export_format}',
                    **cors_headers()
                },
                'body': file_content,
                'isBase64Encoded': True
            }
        else:
            return error_response('Result not found or expired', 404)
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return error_response(str(e))