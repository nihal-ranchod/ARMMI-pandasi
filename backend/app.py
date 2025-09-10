from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename
from services.data_processor import DataProcessor
from services.query_engine import QueryEngine
from utils.file_validator import FileValidator
import logging
import numpy as np

app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/templates')
CORS(app)

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
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), '..', 'uploads')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

data_processor = DataProcessor(app.config['UPLOAD_FOLDER'])
query_engine = QueryEngine()
file_validator = FileValidator()

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
    try:
        datasets = data_processor.list_datasets()
        clean_datasets = clean_for_json(datasets)
        return jsonify({'success': True, 'datasets': clean_datasets})
    except Exception as e:
        logger.error(f"Error getting datasets: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
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
        
        # Process and save file
        dataset_info = data_processor.save_dataset(file)
        # Clean the dataset info to remove NaN values
        clean_dataset_info = clean_for_json(dataset_info)
        return jsonify({'success': True, 'dataset': clean_dataset_info})
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/preview', methods=['GET'])
def preview_dataset(dataset_id):
    try:
        preview_data = data_processor.get_dataset_preview(dataset_id)
        clean_preview_data = clean_for_json(preview_data)
        return jsonify({'success': True, 'preview': clean_preview_data})
    except Exception as e:
        logger.error(f"Error previewing dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/stats', methods=['GET'])
def get_dataset_stats(dataset_id):
    try:
        stats = data_processor.get_dataset_stats(dataset_id)
        clean_stats = clean_for_json(stats)
        return jsonify({'success': True, 'stats': clean_stats})
    except Exception as e:
        logger.error(f"Error getting dataset stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query_data():
    try:
        data = request.get_json()
        query_text = data.get('query', '')
        dataset_ids = data.get('datasets', [])
        
        if not query_text:
            return jsonify({'success': False, 'error': 'Query text is required'}), 400
        
        if not dataset_ids:
            return jsonify({'success': False, 'error': 'At least one dataset must be selected'}), 400
        
        # Execute query
        result = query_engine.execute_query(query_text, dataset_ids, data_processor)
        clean_result = clean_for_json(result)
        return jsonify({'success': True, 'result': clean_result})
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>/rename', methods=['PUT'])
def rename_dataset(dataset_id):
    try:
        data = request.get_json()
        new_name = data.get('name', '').strip()
        
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400
        
        success = data_processor.rename_dataset(dataset_id, new_name)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error renaming dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    try:
        success = data_processor.delete_dataset(dataset_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Dataset not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting dataset: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/query-history', methods=['GET'])
def get_query_history():
    try:
        history = query_engine.get_query_history()
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        logger.error(f"Error getting query history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export/<result_id>', methods=['GET'])
def export_results(result_id):
    try:
        export_format = request.args.get('format', 'csv')
        file_path = query_engine.export_result(result_id, export_format)
        
        if file_path and os.path.exists(file_path):
            return send_from_directory(
                os.path.dirname(file_path),
                os.path.basename(file_path),
                as_attachment=True
            )
        else:
            return jsonify({'success': False, 'error': 'Result not found or expired'}), 404
            
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/charts/<filename>')
def serve_chart(filename):
    try:
        charts_dir = '/home/nranchod/ARMMI-pandasi/exports/charts'
        return send_from_directory(charts_dir, filename)
    except Exception as e:
        logger.error(f"Error serving chart: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)