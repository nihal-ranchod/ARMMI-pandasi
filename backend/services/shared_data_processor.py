import pandas as pd
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import logging
from services.mongodb import mongodb
from bson import ObjectId

logger = logging.getLogger(__name__)

class SharedDataProcessor:
    """Handles shared datasets that all users can query from"""
    
    def __init__(self):
        self.collection_name = 'shared_datasets'
    
    def _convert_objectid(self, obj):
        """Convert ObjectId to string for JSON serialization"""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_objectid(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_objectid(item) for item in obj]
        return obj
    
    def save_shared_dataset(self, file, admin_user):
        """Save dataset to shared knowledge base (admin only)"""
        if not admin_user.is_admin():
            raise PermissionError("Only admin users can upload to shared knowledge base")
        
        dataset_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        try:
            # Load and analyze dataset directly from memory
            if filename.endswith('.csv'):
                # Try different encodings for CSV files
                df = None
                encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                
                for encoding in encodings_to_try:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, encoding=encoding)
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
                file.seek(0)
                df = pd.read_excel(file)
            else:
                raise ValueError("Unsupported file format")
            
            # Create shared dataset metadata
            dataset_info = {
                'dataset_id': dataset_id,
                'name': filename.rsplit('.', 1)[0],
                'original_filename': filename,
                'upload_date': datetime.now(),
                'uploaded_by': admin_user.user_id,
                'uploaded_by_name': admin_user.name,
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'column_types': df.dtypes.astype(str).to_dict(),
                'size_bytes': len(str(df.to_csv()).encode('utf-8')),
                'missing_values': df.isnull().sum().to_dict(),
                'preview': df.head(5).fillna('').to_dict('records'),
                'is_active': True
            }
            
            # Store the full dataset using chunked storage
            full_data = df.fillna('').to_dict('records')
            
            try:
                # Calculate chunk size based on estimated document size
                estimated_size = len(str(full_data).encode('utf-8'))
                chunk_size = max(100, min(10000, int(10 * 1024 * 1024 / (estimated_size / len(full_data)))))
                
                logger.info(f"Shared dataset size: {estimated_size} bytes, using chunk size: {chunk_size}")
                
                # Split data into chunks
                chunks = [full_data[i:i + chunk_size] for i in range(0, len(full_data), chunk_size)]
                
                # Store metadata document
                dataset_metadata = {
                    '_id': dataset_id,
                    'dataset_id': dataset_id,
                    'total_chunks': len(chunks),
                    'total_rows': len(full_data),
                    'chunk_size': chunk_size,
                    'created_at': datetime.now(),
                    'is_shared': True
                }
                mongodb.dataset_data.insert_one(dataset_metadata)
                
                # Store each chunk as a separate document
                for i, chunk in enumerate(chunks):
                    chunk_doc = {
                        '_id': f"{dataset_id}_chunk_{i}",
                        'dataset_id': dataset_id,
                        'chunk_index': i,
                        'data': chunk,
                        'created_at': datetime.now(),
                        'is_shared': True
                    }
                    mongodb.dataset_data.insert_one(chunk_doc)
                
                dataset_info['has_full_data'] = True
                dataset_info['is_chunked'] = True
                dataset_info['total_chunks'] = len(chunks)
                logger.info(f"Successfully stored shared dataset in {len(chunks)} chunks")
                
            except Exception as e:
                logger.warning(f"Could not store full shared dataset data: {str(e)}")
                dataset_info['has_full_data'] = False
                dataset_info['is_chunked'] = False
            
            # Store shared dataset metadata
            shared_collection = mongodb.get_collection(self.collection_name)
            result = shared_collection.insert_one(dataset_info)
            
            # Convert ObjectId to string for JSON serialization
            dataset_info = self._convert_objectid(dataset_info)
            
            logger.info(f"📊 Added shared dataset '{dataset_info['name']}' by admin {admin_user.email}")
            return dataset_info
            
        except Exception as e:
            # Clean up any partial data
            try:
                if 'dataset_info' in locals() and dataset_info.get('is_chunked'):
                    mongodb.dataset_data.delete_one({'_id': dataset_id})
                    mongodb.dataset_data.delete_many({
                        'dataset_id': dataset_id,
                        'is_shared': True,
                        '_id': {'$regex': f'^{dataset_id}_chunk_'}
                    })
            except:
                pass
            raise e
    
    def list_shared_datasets(self):
        """List all active shared datasets"""
        try:
            shared_collection = mongodb.get_collection(self.collection_name)
            datasets = list(shared_collection.find({'is_active': True}))
            
            datasets_list = []
            for dataset in datasets:
                # Convert ObjectIds to strings
                dataset = self._convert_objectid(dataset)
                
                dataset_summary = {
                    'id': dataset['dataset_id'],
                    'name': dataset['name'],
                    'original_filename': dataset['original_filename'],
                    'upload_date': dataset['upload_date'].isoformat() if isinstance(dataset['upload_date'], datetime) else dataset['upload_date'],
                    'uploaded_by': dataset.get('uploaded_by_name', 'Unknown'),
                    'rows': dataset['rows'],
                    'columns': dataset['columns'],
                    'size_bytes': dataset['size_bytes']
                }
                datasets_list.append(dataset_summary)
            
            # Sort by upload date (newest first)
            return sorted(datasets_list, key=lambda x: x['upload_date'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing shared datasets: {str(e)}")
            return []
    
    def get_shared_dataset_info(self, dataset_id):
        """Get shared dataset info by ID"""
        try:
            shared_collection = mongodb.get_collection(self.collection_name)
            result = shared_collection.find_one({'dataset_id': dataset_id, 'is_active': True})
            return self._convert_objectid(result) if result else None
        except Exception as e:
            logger.error(f"Error getting shared dataset info: {str(e)}")
            return None
    
    def load_shared_dataset(self, dataset_id):
        """Load shared dataset from MongoDB"""
        dataset_info = self.get_shared_dataset_info(dataset_id)
        if not dataset_info:
            raise ValueError("Shared dataset not found")
        
        try:
            # Check if dataset is chunked
            if dataset_info.get('is_chunked', False):
                # Load chunked data
                logger.info(f"Loading chunked shared dataset {dataset_id}")
                
                # Get metadata
                metadata = mongodb.dataset_data.find_one({
                    '_id': dataset_id,
                    'is_shared': True
                })
                
                if metadata and 'total_chunks' in metadata:
                    # Load all chunks
                    all_data = []
                    for i in range(metadata['total_chunks']):
                        chunk_doc = mongodb.dataset_data.find_one({
                            '_id': f"{dataset_id}_chunk_{i}",
                            'is_shared': True
                        })
                        if chunk_doc and 'data' in chunk_doc:
                            all_data.extend(chunk_doc['data'])
                    
                    if all_data:
                        df = pd.DataFrame(all_data)
                        logger.info(f"Successfully loaded {len(all_data)} rows from {metadata['total_chunks']} chunks (shared dataset)")
                        return df
                    else:
                        raise ValueError("No chunk data found for shared dataset")
                else:
                    raise ValueError("Chunk metadata not found for shared dataset")
            else:
                # Load non-chunked data (legacy)
                dataset_data = mongodb.dataset_data.find_one({
                    '_id': dataset_id,
                    'is_shared': True
                })
                if dataset_data and 'data' in dataset_data:
                    df = pd.DataFrame(dataset_data['data'])
                    return df
                else:
                    raise ValueError("Full data not found for shared dataset")
                    
        except Exception as e:
            logger.error(f"Error loading shared dataset {dataset_id}: {str(e)}")
            raise ValueError(f"Failed to load shared dataset: {str(e)}")
    
    def load_all_shared_datasets(self):
        """Load all active shared datasets and return as a dictionary"""
        datasets = {}
        shared_datasets = self.list_shared_datasets()
        
        for dataset_summary in shared_datasets:
            try:
                df = self.load_shared_dataset(dataset_summary['id'])
                datasets[dataset_summary['name']] = df
                logger.info(f"Loaded shared dataset '{dataset_summary['name']}' ({len(df)} rows)")
            except Exception as e:
                logger.error(f"Error loading shared dataset {dataset_summary['id']}: {str(e)}")
                continue
                
        return datasets
    
    def delete_shared_dataset(self, dataset_id, admin_user):
        """Delete shared dataset (admin only)"""
        if not admin_user.is_admin():
            raise PermissionError("Only admin users can delete shared datasets")
        
        dataset_info = self.get_shared_dataset_info(dataset_id)
        if not dataset_info:
            return False
        
        try:
            # Mark as inactive instead of deleting (soft delete)
            shared_collection = mongodb.get_collection(self.collection_name)
            result = shared_collection.update_one(
                {'dataset_id': dataset_id},
                {'$set': {'is_active': False, 'deleted_by': admin_user.user_id, 'deleted_at': datetime.now()}}
            )
            
            if result.modified_count > 0:
                # Also clean up the actual data
                if dataset_info.get('has_full_data', False):
                    # Delete metadata document
                    mongodb.dataset_data.delete_one({
                        '_id': dataset_id,
                        'is_shared': True
                    })
                    
                    # If chunked, delete all chunk documents
                    if dataset_info.get('is_chunked', False):
                        result = mongodb.dataset_data.delete_many({
                            'dataset_id': dataset_id,
                            'is_shared': True,
                            '_id': {'$regex': f'^{dataset_id}_chunk_'}
                        })
                        logger.info(f"Deleted {result.deleted_count} chunks for shared dataset {dataset_id}")
                
                logger.info(f"Deleted shared dataset {dataset_id} by admin {admin_user.email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting shared dataset: {str(e)}")
            return False
    
    def rename_shared_dataset(self, dataset_id, new_name, admin_user):
        """Rename shared dataset (admin only)"""
        if not admin_user.is_admin():
            raise PermissionError("Only admin users can rename shared datasets")
        
        try:
            shared_collection = mongodb.get_collection(self.collection_name)
            result = shared_collection.update_one(
                {'dataset_id': dataset_id, 'is_active': True},
                {'$set': {'name': new_name, 'modified_by': admin_user.user_id, 'modified_at': datetime.now()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error renaming shared dataset: {str(e)}")
            return False