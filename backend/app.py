from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
import pandas as pd
import os
import json
from datetime import datetime, timedelta
import uuid
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from services.user_data_processor import UserDataProcessor
from services.shared_data_processor import SharedDataProcessor
from services.user_query_engine import UserQueryEngine
from utils.file_validator import FileValidator
from auth.routes import auth_bp
from auth.decorators import login_required, admin_required, get_current_user
from auth.models import User
from services.mongodb import mongodb
import logging
import numpy as np

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')

# Configure session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ammina-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'ammina:'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

Session(app)
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# Custom JSON encoder to handle NaN values
class NaNSafeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if pd.isna(obj) or (isinstance(obj, float) and np.isnan(obj)):
            return None
        return super().default(obj)

app.json_encoder = NaNSafeJSONEncoder

def clean_for_json(data):
    """Recursively clean data structure to remove NaN values"""
    if isinstance(data, dict):
        return {k: clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_for_json(item) for item in data]
    elif pd.isna(data) or (isinstance(data, float) and np.isnan(data)):
        return None
    else:
        return data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
# Initialize services
user_data_processor = UserDataProcessor()
shared_data_processor = SharedDataProcessor()
user_query_engine = UserQueryEngine()
file_validator = FileValidator()

# Register authentication blueprint
app.register_blueprint(auth_bp)

@app.route('/')
def index():
    # Always redirect to login page for unauthenticated users
    return send_from_directory('../frontend', 'login.html')

@app.route('/login')
def login_page():
    return send_from_directory('../frontend', 'login.html')

@app.route('/app')
@login_required
def app_page():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/datasets', methods=['GET'])
@login_required
def get_datasets():
    try:
        current_user = get_current_user()
        datasets = user_data_processor.list_datasets(current_user)
        clean_datasets = clean_for_json(datasets)
        return jsonify({'success': True, 'datasets': clean_datasets})
    except Exception as e:
        logger.error(f"Error getting datasets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_dataset():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file
        validation_result = file_validator.validate_file(file)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']}), 400
        
        # Process and save file for current user
        current_user = get_current_user()
        dataset_info = user_data_processor.save_dataset(file, current_user)
        # Clean the dataset info to remove NaN values
        clean_dataset_info = clean_for_json(dataset_info)
        return jsonify({'success': True, 'dataset': clean_dataset_info})
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/preview', methods=['GET'])
@login_required
def preview_dataset(dataset_id):
    try:
        current_user = get_current_user()
        preview_data = user_data_processor.get_dataset_preview(dataset_id, current_user)
        clean_preview_data = clean_for_json(preview_data)
        return jsonify({'success': True, 'preview': clean_preview_data})
    except Exception as e:
        logger.error(f"Error previewing dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/stats', methods=['GET'])
@login_required
def get_dataset_stats(dataset_id):
    try:
        current_user = get_current_user()
        stats = user_data_processor.get_dataset_stats(dataset_id, current_user)
        clean_stats = clean_for_json(stats)
        return jsonify({'success': True, 'stats': clean_stats})
    except Exception as e:
        logger.error(f"Error getting dataset stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
@login_required
def query_data():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        
        if not query_text:
            return jsonify({'success': False, 'error': 'Query text is required'}), 400
        
        # Execute query for current user using all shared datasets
        current_user = get_current_user()
        result = user_query_engine.execute_query(query_text, current_user, shared_data_processor)
        clean_result = clean_for_json(result)
        return jsonify({'success': True, 'result': clean_result})
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/rename', methods=['PUT'])
@login_required
def rename_dataset(dataset_id):
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400
        
        current_user = get_current_user()
        success = user_data_processor.rename_dataset(dataset_id, new_name, current_user)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error renaming dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>', methods=['DELETE'])
@login_required
def delete_dataset(dataset_id):
    try:
        current_user = get_current_user()
        success = user_data_processor.delete_dataset(dataset_id, current_user)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query-history', methods=['GET'])
@login_required
def get_query_history():
    try:
        current_user = get_current_user()
        history = user_query_engine.get_query_history(current_user)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        logger.error(f"Error getting query history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query-history', methods=['DELETE'])
@login_required
def clear_query_history():
    try:
        current_user = get_current_user()
        success = user_query_engine.clear_query_history(current_user)
        if success:
            return jsonify({'success': True, 'message': 'Query history cleared successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to clear query history'}), 500
    except Exception as e:
        logger.error(f"Error clearing query history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query-result/<query_id>', methods=['GET'])
@login_required
def get_query_result(query_id):
    try:
        current_user = get_current_user()
        
        # Find the query result in user's history
        query_result = None
        for query in current_user.query_history:
            if query.get('query_id') == query_id and 'full_result' in query:
                query_result = query['full_result']
                break
        
        if query_result:
            clean_result = clean_for_json(query_result)
            return jsonify({'success': True, 'result': clean_result})
        else:
            return jsonify({'success': False, 'error': 'Query result not found'}), 404
            
    except Exception as e:
        logger.error(f"Error getting query result: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/<result_id>', methods=['GET'])
@login_required
def export_results(result_id):
    try:
        # Export functionality is currently not implemented for MongoDB storage
        # TODO: Implement export by generating files from MongoDB data on-demand
        return jsonify({'success': False, 'error': 'Export functionality not implemented for MongoDB storage'}), 501
            
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Chart serving route
@app.route('/api/charts/<chart_id>', methods=['GET'])
@login_required
def serve_chart(chart_id):
    try:
        current_user = get_current_user()

        # Find the chart data in user's query history
        chart_data = None
        for query in current_user.query_history:
            if 'full_result' in query and 'visualizations' in query['full_result']:
                for viz in query['full_result']['visualizations']:
                    if viz.get('id') == chart_id:
                        chart_data = viz.get('data')
                        break
                if chart_data:
                    break

        if chart_data:
            import base64
            from flask import Response

            # Decode base64 image data
            image_data = base64.b64decode(chart_data)

            return Response(
                image_data,
                mimetype='image/png',
                headers={'Content-Type': 'image/png'}
            )
        else:
            return jsonify({'success': False, 'error': 'Chart not found'}), 404

    except Exception as e:
        logger.error(f"Error serving chart: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Admin-only routes for shared dataset management
@app.route('/api/admin/shared-datasets', methods=['GET'])
@admin_required
def get_shared_datasets():
    try:
        datasets = shared_data_processor.list_shared_datasets()
        return jsonify({'success': True, 'datasets': datasets})
    except Exception as e:
        logger.error(f"Error getting shared datasets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/shared-datasets/upload', methods=['POST'])
@admin_required
def upload_shared_dataset():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file
        validation_result = file_validator.validate_file(file)
        if not validation_result['valid']:
            return jsonify({'success': False, 'error': validation_result['error']}), 400
        
        # Process and save file to shared collection
        current_user = get_current_user()
        dataset_info = shared_data_processor.save_shared_dataset(file, current_user)
        clean_dataset_info = clean_for_json(dataset_info)
        return jsonify({'success': True, 'dataset': clean_dataset_info})
        
    except Exception as e:
        logger.error(f"Error uploading shared dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/shared-datasets/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_shared_dataset(dataset_id):
    try:
        current_user = get_current_user()
        success = shared_data_processor.delete_shared_dataset(dataset_id, current_user)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Shared dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting shared dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/shared-datasets/<dataset_id>/rename', methods=['PUT'])
@admin_required
def rename_shared_dataset(dataset_id):
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400
        
        current_user = get_current_user()
        success = shared_data_processor.rename_shared_dataset(dataset_id, new_name, current_user)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Shared dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error renaming shared dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Regular user route to view available shared datasets (read-only)
@app.route('/api/shared-datasets', methods=['GET'])
@login_required
def get_available_datasets():
    try:
        datasets = shared_data_processor.list_shared_datasets()
        return jsonify({'success': True, 'datasets': datasets})
    except Exception as e:
        logger.error(f"Error getting available datasets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    try:
        current_user = get_current_user()
        user_info = {
            'user_id': current_user.user_id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role,
            'is_admin': current_user.is_admin(),
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': current_user.last_login.isoformat() if current_user.last_login else None
        }
        return jsonify({'success': True, 'user': user_info})
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # Test MongoDB connection at startup (only in main process, not reloader)
    try:
        import os
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            logger.info("🚀 Starting AMMINA Platform...")
            logger.info("🔗 Testing MongoDB connection...")
            
        # Test the connection by accessing the database
        test_collection = mongodb.get_collection('test')
        
        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            logger.info("✅ MongoDB connection successful - ready to serve requests!")
            logger.info("🌐 Starting Flask development server on http://127.0.0.1:5000")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {str(e)}")
        logger.error("🛑 Application cannot start without database connection")
        exit(1)
    
    # Use environment variables for production
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)