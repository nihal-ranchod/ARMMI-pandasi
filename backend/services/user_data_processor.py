import pandas as pd
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class UserDataProcessor:
    def __init__(self):
        # All data is now stored in MongoDB, no local file storage needed
        pass
    
    
    def save_dataset(self, file, user):
        """Save dataset for a specific user"""
        dataset_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        # Load and analyze dataset directly from memory
        try:
            if filename.endswith('.csv'):
                # Try different encodings for CSV files
                df = None
                encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                
                for encoding in encodings_to_try:
                    try:
                        # Reset file pointer
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
            
            # Create dataset metadata
            dataset_info = {
                'dataset_id': dataset_id,
                'name': filename.rsplit('.', 1)[0],
                'original_filename': filename,
                'upload_date': datetime.now(),  # MongoDB will handle timezone
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'column_types': df.dtypes.astype(str).to_dict(),
                'size_bytes': len(str(df.to_csv()).encode('utf-8')),  # Estimate size from CSV representation
                'missing_values': df.isnull().sum().to_dict(),
                'preview': df.head(5).fillna('').to_dict('records')
            }
            
            # Store the full dataset using chunked storage to handle large files
            from services.mongodb import mongodb
            full_data = df.fillna('').to_dict('records')
            
            try:
                # Calculate chunk size based on estimated document size
                # Aim for chunks under 10MB to stay well below 16MB limit
                estimated_size = len(str(full_data).encode('utf-8'))
                chunk_size = max(100, min(10000, int(10 * 1024 * 1024 / (estimated_size / len(full_data)))))
                
                logger.info(f"Dataset size: {estimated_size} bytes, using chunk size: {chunk_size}")
                
                # Split data into chunks
                chunks = [full_data[i:i + chunk_size] for i in range(0, len(full_data), chunk_size)]
                
                # Store metadata document
                dataset_metadata = {
                    '_id': dataset_id,
                    'user_id': user.user_id,
                    'dataset_id': dataset_id,
                    'total_chunks': len(chunks),
                    'total_rows': len(full_data),
                    'chunk_size': chunk_size,
                    'created_at': datetime.now()
                }
                mongodb.dataset_data.insert_one(dataset_metadata)
                
                # Store each chunk as a separate document
                for i, chunk in enumerate(chunks):
                    chunk_doc = {
                        '_id': f"{dataset_id}_chunk_{i}",
                        'dataset_id': dataset_id,
                        'user_id': user.user_id,
                        'chunk_index': i,
                        'data': chunk,
                        'created_at': datetime.now()
                    }
                    mongodb.dataset_data.insert_one(chunk_doc)
                
                dataset_info['has_full_data'] = True
                dataset_info['is_chunked'] = True
                dataset_info['total_chunks'] = len(chunks)
                logger.info(f"Successfully stored dataset in {len(chunks)} chunks")
                
            except Exception as e:
                logger.warning(f"Could not store full dataset data: {str(e)}")
                dataset_info['has_full_data'] = False
                dataset_info['is_chunked'] = False
            
            # Add dataset metadata to user document
            if user.add_dataset(dataset_info):
                return dataset_info
            else:
                # Clean up dataset data if user document update fails
                if dataset_info.get('has_full_data'):
                    try:
                        mongodb.dataset_data.delete_one({'_id': dataset_id})
                    except:
                        pass
                raise Exception("Failed to save dataset metadata")
            
        except Exception as e:
            raise e
    
    def list_datasets(self, user):
        """List all datasets for a user"""
        datasets_list = []
        for dataset in user.datasets:
            dataset_summary = {
                'id': dataset['dataset_id'],
                'name': dataset['name'],
                'original_filename': dataset['original_filename'],
                'upload_date': dataset['upload_date'].isoformat() if isinstance(dataset['upload_date'], datetime) else dataset['upload_date'],
                'rows': dataset['rows'],
                'columns': dataset['columns'],
                'size_bytes': dataset['size_bytes']
            }
            datasets_list.append(dataset_summary)
        
        # Sort by upload date (newest first)
        return sorted(datasets_list, key=lambda x: x['upload_date'], reverse=True)
    
    def get_dataset_preview(self, dataset_id, user):
        """Get dataset preview for a user"""
        dataset = user.get_dataset_by_id(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        
        # Ensure preview data doesn't contain NaN values
        preview_data = dataset['preview']
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
            'columns': dataset['column_names'],
            'data': cleaned_preview,
            'total_rows': dataset['rows']
        }
    
    def get_dataset_stats(self, dataset_id, user):
        """Get dataset statistics for a user"""
        dataset = user.get_dataset_by_id(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        
        # Load full dataset for advanced stats
        try:
            df = self.load_dataset(dataset_id, user)
            
            stats = {
                'basic_info': {
                    'rows': dataset['rows'],
                    'columns': dataset['columns'],
                    'size_bytes': dataset['size_bytes'],
                    'column_types': dataset['column_types']
                },
                'missing_values': dataset['missing_values'],
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
    
    
    def load_datasets(self, dataset_ids, user):
        """Load multiple datasets for a user"""
        datasets = {}
        for dataset_id in dataset_ids:
            try:
                df = self.load_dataset(dataset_id, user)
                dataset = user.get_dataset_by_id(dataset_id)
                datasets[dataset['name']] = df
            except Exception as e:
                logger.error(f"Error loading dataset {dataset_id}: {str(e)}")
                continue
        return datasets
    
    def rename_dataset(self, dataset_id, new_name, user):
        """Rename a dataset for a user"""
        update_data = {'name': new_name}
        return user.update_dataset(dataset_id, update_data)
    
    def delete_dataset(self, dataset_id, user):
        """Delete a dataset for a user"""
        dataset = user.get_dataset_by_id(dataset_id)
        if not dataset:
            return False
        
        # Remove full data from separate collection if it exists
        if dataset.get('has_full_data', False):
            try:
                from services.mongodb import mongodb
                
                # Delete metadata document
                mongodb.dataset_data.delete_one({
                    '_id': dataset_id,
                    'user_id': user.user_id
                })
                
                # If chunked, delete all chunk documents
                if dataset.get('is_chunked', False):
                    # Delete all chunks for this dataset
                    result = mongodb.dataset_data.delete_many({
                        'dataset_id': dataset_id,
                        'user_id': user.user_id,
                        '_id': {'$regex': f'^{dataset_id}_chunk_'}
                    })
                    logger.info(f"Deleted {result.deleted_count} chunks for dataset {dataset_id}")
                
                logger.info(f"Deleted full dataset data for {dataset_id}")
            except Exception as e:
                logger.warning(f"Could not delete dataset data: {str(e)}")
        
        # Remove from user document
        return user.remove_dataset(dataset_id)
    
    def load_dataset(self, dataset_id, user):
        """Load dataset from MongoDB for query processing"""
        dataset_info = user.get_dataset_by_id(dataset_id)
        if not dataset_info:
            raise ValueError("Dataset file not found")
        
        # Get the raw data from MongoDB
        try:
            # Try to load from separate dataset_data collection first
            if dataset_info.get('has_full_data', False):
                from services.mongodb import mongodb
                
                # Check if dataset is chunked
                if dataset_info.get('is_chunked', False):
                    # Load chunked data
                    logger.info(f"Loading chunked dataset {dataset_id}")
                    
                    # Get metadata
                    metadata = mongodb.dataset_data.find_one({
                        '_id': dataset_id,
                        'user_id': user.user_id
                    })
                    
                    if metadata and 'total_chunks' in metadata:
                        # Load all chunks
                        all_data = []
                        for i in range(metadata['total_chunks']):
                            chunk_doc = mongodb.dataset_data.find_one({
                                '_id': f"{dataset_id}_chunk_{i}",
                                'user_id': user.user_id
                            })
                            if chunk_doc and 'data' in chunk_doc:
                                all_data.extend(chunk_doc['data'])
                        
                        if all_data:
                            df = pd.DataFrame(all_data)
                            logger.info(f"Successfully loaded {len(all_data)} rows from {metadata['total_chunks']} chunks")
                        else:
                            df = pd.DataFrame(dataset_info['preview'])
                            logger.warning(f"No chunk data found for dataset {dataset_id}, using preview data")
                    else:
                        df = pd.DataFrame(dataset_info['preview'])
                        logger.warning(f"Chunk metadata not found for dataset {dataset_id}, using preview data")
                else:
                    # Load non-chunked data (legacy)
                    dataset_data = mongodb.dataset_data.find_one({
                        '_id': dataset_id,
                        'user_id': user.user_id
                    })
                    if dataset_data and 'data' in dataset_data:
                        df = pd.DataFrame(dataset_data['data'])
                    else:
                        # Fall back to preview if full data not found
                        df = pd.DataFrame(dataset_info['preview'])
                        logger.warning(f"Full data not found for dataset {dataset_id}, using preview data")
            elif 'data' in dataset_info:
                # Full dataset data stored in user document (legacy)
                df = pd.DataFrame(dataset_info['data'])
            elif 'preview' in dataset_info:
                # Use preview data as fallback
                df = pd.DataFrame(dataset_info['preview'])
                logger.warning(f"Using preview data for dataset {dataset_id} - consider re-uploading for full data")
            else:
                raise ValueError("No data found in dataset")
            
            # Restore original column names and types if available
            if 'column_names' in dataset_info:
                df.columns = dataset_info['column_names'][:len(df.columns)]
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {str(e)}")
            raise ValueError(f"Dataset file not found")
    
    def get_dataset_info(self, dataset_id, user):
        """Get dataset info for a user"""
        return user.get_dataset_by_id(dataset_id)