import pandas as pd
import os
import json
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.metadata_file = os.path.join(upload_folder, 'datasets_metadata.json')
        self.datasets = self._load_metadata()
    
    def _load_metadata(self):
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata: {str(e)}")
                return {}
        return {}
    
    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.datasets, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def save_dataset(self, file):
        dataset_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, f"{dataset_id}_{filename}")
        
        # Save file
        file.save(file_path)
        
        # Load and analyze dataset
        try:
            if filename.endswith('.csv'):
                # Try different encodings for CSV files
                df = None
                encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                
                for encoding in encodings_to_try:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        logger.info(f"Successfully read CSV with {encoding} encoding")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                            raise e
                        continue
                
                if df is None:
                    raise ValueError("Unable to read CSV file with any supported encoding")
                    
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            # Create metadata
            dataset_info = {
                'id': dataset_id,
                'name': filename.rsplit('.', 1)[0],
                'original_filename': filename,
                'file_path': file_path,
                'upload_date': datetime.now().isoformat(),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'column_types': df.dtypes.astype(str).to_dict(),
                'size_bytes': os.path.getsize(file_path),
                'missing_values': df.isnull().sum().to_dict(),
                'preview': df.head(5).fillna('').to_dict('records')
            }
            
            self.datasets[dataset_id] = dataset_info
            self._save_metadata()
            
            return dataset_info
            
        except Exception as e:
            # Clean up file if processing failed
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    def list_datasets(self):
        # Return datasets without preview data for listing
        datasets_list = []
        for dataset_id, dataset_info in self.datasets.items():
            dataset_summary = {
                'id': dataset_info['id'],
                'name': dataset_info['name'],
                'original_filename': dataset_info['original_filename'],
                'upload_date': dataset_info['upload_date'],
                'rows': dataset_info['rows'],
                'columns': dataset_info['columns'],
                'size_bytes': dataset_info['size_bytes']
            }
            datasets_list.append(dataset_summary)
        
        return sorted(datasets_list, key=lambda x: x['upload_date'], reverse=True)
    
    def get_dataset_preview(self, dataset_id):
        if dataset_id not in self.datasets:
            raise ValueError("Dataset not found")
        
        dataset_info = self.datasets[dataset_id]
        
        # Ensure preview data doesn't contain NaN values
        preview_data = dataset_info['preview']
        cleaned_preview = []
        for row in preview_data:
            cleaned_row = {}
            for key, value in row.items():
                if pd.isna(value):
                    cleaned_row[key] = ''
                else:
                    cleaned_row[key] = value
            cleaned_preview.append(cleaned_row)
        
        return {
            'columns': dataset_info['column_names'],
            'data': cleaned_preview,
            'total_rows': dataset_info['rows']
        }
    
    def get_dataset_stats(self, dataset_id):
        if dataset_id not in self.datasets:
            raise ValueError("Dataset not found")
        
        dataset_info = self.datasets[dataset_id]
        
        # Load full dataset for advanced stats
        try:
            df = self.load_dataset(dataset_id)
            
            stats = {
                'basic_info': {
                    'rows': dataset_info['rows'],
                    'columns': dataset_info['columns'],
                    'size_bytes': dataset_info['size_bytes'],
                    'column_types': dataset_info['column_types']
                },
                'missing_values': dataset_info['missing_values'],
                'numeric_stats': {},
                'categorical_stats': {}
            }
            
            # Numeric column statistics
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                stats['numeric_stats'][col] = {
                    'mean': float(df[col].mean()) if not df[col].empty else None,
                    'median': float(df[col].median()) if not df[col].empty else None,
                    'std': float(df[col].std()) if not df[col].empty else None,
                    'min': float(df[col].min()) if not df[col].empty else None,
                    'max': float(df[col].max()) if not df[col].empty else None,
                    'unique_count': int(df[col].nunique())
                }
            
            # Categorical column statistics
            categorical_columns = df.select_dtypes(include=['object', 'category']).columns
            for col in categorical_columns:
                unique_values = df[col].value_counts().head(10)
                stats['categorical_stats'][col] = {
                    'unique_count': int(df[col].nunique()),
                    'most_common': unique_values.to_dict()
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating stats: {str(e)}")
            return {'error': str(e)}
    
    def load_dataset(self, dataset_id):
        if dataset_id not in self.datasets:
            raise ValueError("Dataset not found")
        
        dataset_info = self.datasets[dataset_id]
        file_path = dataset_info['file_path']
        
        if not os.path.exists(file_path):
            raise ValueError("Dataset file not found")
        
        filename = dataset_info['original_filename']
        if filename.endswith('.csv'):
            # Try different encodings for CSV files
            encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
            
            for encoding in encodings_to_try:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                        raise e
                    continue
            
            raise ValueError("Unable to read CSV file with any supported encoding")
            
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def rename_dataset(self, dataset_id, new_name):
        if dataset_id not in self.datasets:
            return False
        
        self.datasets[dataset_id]['name'] = new_name
        self._save_metadata()
        return True
    
    def delete_dataset(self, dataset_id):
        if dataset_id not in self.datasets:
            return False
        
        dataset_info = self.datasets[dataset_id]
        file_path = dataset_info['file_path']
        
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from metadata
        del self.datasets[dataset_id]
        self._save_metadata()
        
        return True
    
    def get_dataset_info(self, dataset_id):
        return self.datasets.get(dataset_id, None)