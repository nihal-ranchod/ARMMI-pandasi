import os
import pandas as pd
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    def __init__(self):
        self.allowed_extensions = {'csv', 'xlsx', 'xls'}
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.max_rows = 1000000  # 1 million rows
        self.max_columns = 1000
    
    def validate_file(self, file):
        """
        Validate uploaded file for security and compatibility
        """
        try:
            # Check if file exists
            if not file or file.filename == '':
                return {'valid': False, 'error': 'No file provided'}
            
            # Check file extension
            if not self._is_allowed_file(file.filename):
                return {
                    'valid': False, 
                    'error': f'File type not supported. Allowed types: {", ".join(self.allowed_extensions)}'
                }
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            if file_size > self.max_file_size:
                return {
                    'valid': False, 
                    'error': f'File too large. Maximum size: {self.max_file_size / (1024*1024):.0f}MB'
                }
            
            # Check if file is empty
            if file_size == 0:
                return {'valid': False, 'error': 'File is empty'}
            
            # Validate file content
            content_validation = self._validate_file_content(file)
            if not content_validation['valid']:
                return content_validation
            
            return {'valid': True, 'message': 'File validation successful'}
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    def _is_allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _validate_file_content(self, file):
        """
        Validate the actual content of the file
        """
        try:
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            
            # Reset file pointer
            file.seek(0)
            
            # Try to read the file based on extension with encoding handling
            if file_ext == 'csv':
                # Try different encodings for CSV files
                df = None
                encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                
                for encoding in encodings_to_try:
                    try:
                        file.seek(0)
                        df = pd.read_csv(file, nrows=5, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        # If it's not an encoding error, stop trying other encodings
                        if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                            raise e
                        continue
                
                if df is None:
                    return {'valid': False, 'error': 'Unable to read CSV file. Please ensure it uses standard encoding (UTF-8, Latin-1, etc.)'}
                    
            elif file_ext in ['xlsx', 'xls']:
                # Excel files typically don't have encoding issues
                try:
                    df = pd.read_excel(file, nrows=5)
                except Exception as e:
                    return {'valid': False, 'error': f'Unable to read Excel file: {str(e)}'}
            else:
                return {'valid': False, 'error': 'Unsupported file format'}
            
            # Reset file pointer after reading
            file.seek(0)
            
            # Check if DataFrame is empty
            if df.empty:
                return {'valid': False, 'error': 'File contains no data'}
            
            # Check column count
            if len(df.columns) > self.max_columns:
                return {
                    'valid': False, 
                    'error': f'Too many columns. Maximum allowed: {self.max_columns}'
                }
            
            # Check for duplicate column names
            if len(df.columns) != len(set(df.columns)):
                return {'valid': False, 'error': 'Duplicate column names found'}
            
            # Check for completely empty column names
            empty_cols = [col for col in df.columns if pd.isna(col) or str(col).strip() == '']
            if empty_cols:
                return {'valid': False, 'error': 'Found columns with empty names'}
            
            # For more thorough validation, read the entire file
            file.seek(0)
            try:
                if file_ext == 'csv':
                    # Try different encodings for full CSV file read
                    full_df = None
                    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
                    
                    for encoding in encodings_to_try:
                        try:
                            file.seek(0)
                            full_df = pd.read_csv(file, encoding=encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                        except Exception as e:
                            if 'codec' not in str(e).lower() and 'decode' not in str(e).lower():
                                raise e
                            continue
                    
                    if full_df is None:
                        return {'valid': False, 'error': 'Unable to read CSV file with any supported encoding'}
                        
                elif file_ext in ['xlsx', 'xls']:
                    full_df = pd.read_excel(file)
                
                # Check row count
                if len(full_df) > self.max_rows:
                    return {
                        'valid': False, 
                        'error': f'Too many rows. Maximum allowed: {self.max_rows:,}'
                    }
                
                # Check for pharmaceutical data indicators (optional validation)
                self._validate_pharmaceutical_data(full_df)
                
            except Exception as e:
                return {'valid': False, 'error': f'Error reading file: {str(e)}'}
            finally:
                file.seek(0)  # Reset file pointer
            
            return {'valid': True, 'rows': len(full_df), 'columns': len(full_df.columns)}
            
        except Exception as e:
            logger.error(f"Content validation error: {str(e)}")
            return {'valid': False, 'error': f'Content validation error: {str(e)}'}
    
    def _validate_pharmaceutical_data(self, df):
        """
        Optional validation for pharmaceutical data patterns
        """
        try:
            # Check for common pharmaceutical data indicators
            pharma_indicators = [
                'drug', 'compound', 'molecule', 'patient', 'trial', 'dose',
                'efficacy', 'safety', 'adverse', 'clinical', 'therapeutic',
                'indication', 'treatment', 'study', 'protocol', 'endpoint'
            ]
            
            # Convert column names to lowercase for checking
            column_names_lower = [str(col).lower() for col in df.columns]
            
            # Log potential pharmaceutical data detection (for analytics)
            pharma_score = sum(
                1 for indicator in pharma_indicators 
                if any(indicator in col_name for col_name in column_names_lower)
            )
            
            if pharma_score > 0:
                logger.info(f"Detected potential pharmaceutical data (score: {pharma_score})")
            
        except Exception as e:
            logger.warning(f"Pharmaceutical data validation warning: {str(e)}")
    
    def sanitize_filename(self, filename):
        """
        Sanitize filename for safe storage
        """
        return secure_filename(filename)
    
    def get_file_info(self, file):
        """
        Get basic file information
        """
        try:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            return {
                'filename': file.filename,
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'extension': file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            }
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            return None