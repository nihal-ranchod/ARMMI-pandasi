import pandas as pd
import os
import uuid
import json
from datetime import datetime
try:
    from pandasai import Agent
    from pandasai.llm import OpenAI
except ImportError:
    # Fallback for older versions
    from pandasai import PandasAI
    from pandasai.llm.openai import OpenAI
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import logging

logger = logging.getLogger(__name__)

class UserQueryEngine:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    
    def execute_query(self, query_text, user, shared_data_processor=None):
        """Execute query for a specific user using shared datasets"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.")
        
        result_id = str(uuid.uuid4())
        
        try:
            # Load all shared datasets (new architecture)
            if shared_data_processor:
                datasets_dict = shared_data_processor.load_all_shared_datasets()
                datasets = list(datasets_dict.values())
                dataset_names = list(datasets_dict.keys())
            else:
                # Fallback to old per-user dataset system
                datasets = []
                dataset_names = []
                
                # This maintains backwards compatibility but isn't the intended usage
                for dataset in user.datasets:
                    try:
                        from services.user_data_processor import UserDataProcessor
                        user_data_processor = UserDataProcessor()
                        df = user_data_processor.load_dataset(dataset['dataset_id'], user)
                        datasets.append(df)
                        dataset_names.append(dataset['name'])
                    except Exception as e:
                        logger.error(f"Error loading user dataset {dataset['dataset_id']}: {str(e)}")
                        continue
            
            if not datasets:
                raise ValueError("No datasets available for querying. Please ensure shared datasets are uploaded by an admin.")
            
            # Initialize pandas-ai agent (handle different versions)
            try:
                # Try newer pandasai version (2.x+) with GPT-4o-mini
                llm = OpenAI(api_token=self.openai_api_key, model="gpt-4o-mini")
                agent = Agent(datasets, config={"llm": llm, "verbose": True})
                response = agent.chat(query_text)
            except (ImportError, NameError):
                # Fallback to older version
                llm = OpenAI(api_token=self.openai_api_key, model="gpt-4o-mini")
                pandas_ai = PandasAI(llm, verbose=True)
                if len(datasets) == 1:
                    response = pandas_ai.run(datasets[0], prompt=query_text)
                else:
                    # For multiple datasets, combine them
                    combined_df = pd.concat(datasets, ignore_index=True, sort=False)
                    response = pandas_ai.run(combined_df, prompt=query_text)
            except Exception as e:
                # Try with a simple approach if the advanced method fails
                logger.warning(f"Advanced pandasai method failed, trying simple approach: {str(e)}")
                if len(datasets) == 1:
                    df = datasets[0]
                else:
                    df = pd.concat(datasets, ignore_index=True, sort=False)
                
                # Simple query processing using OpenAI directly
                response = self._simple_query_processing(query_text, df)
            
            # Simple response handling - detect PNG plots from pandas-ai
            actual_response = response
            chart_filename = None
            
            logger.info(f"Raw pandas-ai response: {response}")
            logger.info(f"Response type: {type(response)}")
            
            if isinstance(response, dict) and 'type' in response and 'value' in response:
                logger.info(f"Detected structured response - type: {response['type']}")
                if response['type'] == 'dataframe':
                    actual_response = response['value']
                elif response['type'] == 'plot':
                    # Extract just the filename from the path
                    plot_path = response['value']
                    chart_filename = os.path.basename(plot_path)
                    actual_response = f"Generated chart successfully."
                    logger.info(f"Plot detected! Filename: {chart_filename}")
                else:
                    actual_response = response['value']
            elif isinstance(response, str) and response.endswith('.png'):
                # Handle case where pandas-ai returns just the PNG path as string
                logger.info("Detected PNG file path as string response")
                chart_filename = os.path.basename(response)
                actual_response = f"Generated chart successfully."
                logger.info(f"PNG file detected! Filename: {chart_filename}")
            else:
                logger.info("Response is not a structured dict or PNG path, treating as direct response")
            
            # Create simple result structure
            result = {
                'id': result_id,
                'query': query_text,
                'datasets_used': dataset_names,
                'timestamp': datetime.utcnow().isoformat(),
                'response_type': 'text',
                'response': "No response generated" if actual_response is None else str(actual_response),
                'visualizations': [],
                'data_tables': []
            }
            
            # Add chart if generated
            if chart_filename:
                chart_data = self._encode_chart_to_base64(chart_filename)
                chart_id = str(uuid.uuid4())
                
                result['visualizations'].append({
                    'type': 'chart',
                    'title': 'Generated Chart',
                    'id': chart_id,
                    'data': chart_data,
                    'url': f'/api/charts/{chart_id}'  # This will serve from MongoDB
                })
                result['response_type'] = 'mixed'
                logger.info(f"Added chart visualization with ID: {chart_id}")
            
            # Add DataFrame as table if present
            if isinstance(actual_response, pd.DataFrame):
                result['data_tables'].append({
                    'title': 'Query Results',
                    'data': actual_response.head(100).to_dict('records'),
                    'columns': list(actual_response.columns)
                })
                result['response_type'] = 'mixed'
            
            # Format the text response for better readability
            if actual_response is None:
                response_text = "No response generated"
            else:
                response_text = str(actual_response)
            result['formatted_response'] = self._format_response_text(response_text)
            
            # Results are now stored in MongoDB through query history
            
            # Add to user's query history with full result
            query_info = {
                'query': query_text,
                'datasets_used': dataset_names,
                'success': True,
                'result_summary': None if actual_response is None else str(actual_response)[:500],
                'full_result': result  # Store complete result for history viewing
            }
            
            query_id = user.add_query_to_history(query_info)
            if query_id:
                result['query_id'] = query_id
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            
            # Add failed query to user history
            query_info = {
                'query': query_text,
                'datasets_used': dataset_names,
                'success': False,
                'error': str(e)
            }
            
            user.add_query_to_history(query_info)
            
            raise e
    
    def _encode_chart_to_base64(self, chart_filename):
        """Encode chart file to base64 for MongoDB storage"""
        try:
            chart_path = f'/home/nranchod/ARMMI-pandasi/exports/charts/{chart_filename}'
            
            if os.path.exists(chart_path):
                with open(chart_path, 'rb') as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    
                # Clean up the file after encoding
                os.remove(chart_path)
                logger.info(f"Encoded and removed chart file: {chart_filename}")
                
                return encoded_string
            else:
                logger.warning(f"Chart file not found: {chart_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error encoding chart to base64: {str(e)}")
            return None
    
    def get_query_history(self, user):
        """Get query history for a user"""
        # Sort by timestamp (newest first) and limit to 50 queries
        sorted_history = sorted(
            user.query_history, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:50]
        
        # Format for API response
        formatted_history = []
        for entry in sorted_history:
            formatted_entry = {
                'id': entry.get('query_id', str(uuid.uuid4())),
                'query': entry['query'],
                'datasets': entry.get('datasets_used', []),
                'timestamp': entry['timestamp'].isoformat() if isinstance(entry['timestamp'], datetime) else entry['timestamp'],
                'success': entry['success']
            }
            
            if not entry['success']:
                formatted_entry['error'] = entry.get('error', 'Unknown error')
            
            formatted_history.append(formatted_entry)
        
        return formatted_history
    
    def clear_query_history(self, user):
        """Clear query history for a user"""
        try:
            success = user.clear_query_history()
            if success:
                logger.info(f"Cleared query history for user {user.email}")
            return success
        except Exception as e:
            logger.error(f"Error clearing query history for user {user.email}: {str(e)}")
            return False
    
    def export_result(self, result_id, export_format, user):
        """Export result for a user - now using MongoDB data"""
        # TODO: Implement export functionality using MongoDB data
        # For now, return None to indicate export not available
        logger.info(f"Export requested for result {result_id} in {export_format} format - not implemented yet")
        return None
    
    
    def _simple_query_processing(self, query_text, df):
        """Simple query processing using OpenAI directly when pandasai fails"""
        try:
            from openai import OpenAI as OpenAIClient
            
            client = OpenAIClient(api_key=self.openai_api_key)
            
            # Create a summary of the dataset
            dataset_info = {
                'columns': list(df.columns),
                'shape': df.shape,
                'dtypes': df.dtypes.astype(str).to_dict(),
                'sample_data': df.head(3).to_dict('records') if not df.empty else []
            }
            
            # Prepare prompt for OpenAI
            prompt = f"""
            You are a data analyst. I have a dataset with the following structure:
            
            Columns: {dataset_info['columns']}
            Shape: {dataset_info['shape'][0]} rows, {dataset_info['shape'][1]} columns
            Data types: {dataset_info['dtypes']}
            Sample data: {dataset_info['sample_data']}
            
            User question: {query_text}
            
            Please provide a detailed analysis and answer to the user's question about this pharmaceutical dataset.
            If the question requires specific calculations or data manipulation, describe what would be needed
            and provide insights based on the dataset structure and sample data.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst specializing in pharmaceutical data."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Simple query processing failed: {str(e)}")
            return f"I apologize, but I'm unable to process your query at the moment. The question '{query_text}' could not be analyzed due to technical limitations. Please try rephrasing your question or contact support."
    
    def _format_response_text(self, response_text):
        """Format response text for better readability in the UI"""
        if not response_text or response_text.strip() == "":
            return {"type": "text", "content": "No response generated"}
        
        # Clean up the response
        formatted_text = response_text.strip()
        
        # Check if it's already formatted text with structure
        if '\n' in formatted_text:
            # Split into paragraphs and format
            paragraphs = [p.strip() for p in formatted_text.split('\n') if p.strip()]
            
            formatted_content = []
            for para in paragraphs:
                # Check if it looks like a header (short line, ends with colon, etc.)
                if len(para) < 100 and (para.endswith(':') or para.isupper() or para.startswith('###')):
                    formatted_content.append({"type": "header", "content": para.replace('###', '').strip()})
                # Check if it looks like a list item
                elif para.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                    formatted_content.append({"type": "list_item", "content": para})
                # Regular paragraph
                else:
                    formatted_content.append({"type": "paragraph", "content": para})
            
            return {"type": "structured", "content": formatted_content}
        else:
            # Single paragraph response
            return {"type": "text", "content": formatted_text}