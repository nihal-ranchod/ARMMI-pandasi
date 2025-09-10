import pandas as pd
import os
import json
import uuid
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

class QueryEngine:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.query_history_file = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'query_history.json')
        self.results_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads', 'results')
        self.history = self._load_history()
        
        os.makedirs(self.results_folder, exist_ok=True)
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
    
    def _load_history(self):
        if os.path.exists(self.query_history_file):
            try:
                with open(self.query_history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading query history: {str(e)}")
                return []
        return []
    
    def _save_history(self):
        try:
            with open(self.query_history_file, 'w') as f:
                json.dump(self.history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving query history: {str(e)}")
    
    def execute_query(self, query_text, dataset_ids, data_processor):
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.")
        
        result_id = str(uuid.uuid4())
        
        try:
            # Load datasets
            datasets = []
            dataset_names = []
            
            for dataset_id in dataset_ids:
                df = data_processor.load_dataset(dataset_id)
                dataset_info = data_processor.get_dataset_info(dataset_id)
                datasets.append(df)
                dataset_names.append(dataset_info['name'])
            
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
                'timestamp': datetime.now().isoformat(),
                'response_type': 'text',
                'response': str(actual_response) if actual_response is not None else "No response generated",
                'visualizations': [],
                'data_tables': []
            }
            
            # Add chart if generated
            if chart_filename:
                result['visualizations'].append({
                    'type': 'chart',
                    'title': 'Generated Chart',
                    'url': f'/api/charts/{chart_filename}'
                })
                result['response_type'] = 'mixed'
                logger.info(f"Added chart visualization: {chart_filename}")
            
            # Add DataFrame as table if present
            if isinstance(actual_response, pd.DataFrame):
                result['data_tables'].append({
                    'title': 'Query Results',
                    'data': actual_response.head(100).to_dict('records'),
                    'columns': list(actual_response.columns)
                })
                result['response_type'] = 'mixed'
            
            # Format the text response for better readability
            result['formatted_response'] = self._format_response_text(str(response) if response is not None else "No response generated")
            
            # Save result for export functionality
            self._save_result(result_id, result, datasets)
            
            # Add to history
            history_entry = {
                'id': result_id,
                'query': query_text,
                'datasets': dataset_names,
                'timestamp': result['timestamp'],
                'success': True
            }
            self.history.append(history_entry)
            self._save_history()
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            
            # Add failed query to history
            history_entry = {
                'id': result_id,
                'query': query_text,
                'datasets': dataset_names,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
            self.history.append(history_entry)
            self._save_history()
            
            raise e
    
    def _create_visualizations(self, query, datasets, response):
        visualizations = []
        data_tables = []
        
        # Keywords that suggest visualization needs
        viz_keywords = [
            'plot', 'chart', 'graph', 'visualize', 'show', 'display',
            'trend', 'distribution', 'correlation', 'comparison',
            'histogram', 'scatter', 'bar', 'line', 'analyze', 'analysis'
        ]
        
        # Always try to create visualizations for data analysis queries
        should_visualize = any(keyword in query.lower() for keyword in viz_keywords) or len(datasets) > 0
        
        try:
            # Combine all datasets for analysis
            if len(datasets) == 1:
                df = datasets[0]
            else:
                # For multiple datasets, create a simple concatenation
                df = pd.concat(datasets, ignore_index=True, sort=False)
            
            # Generate visualizations based on query content and data
            if should_visualize:
                # Try different types of visualizations
                if 'distribution' in query.lower() or 'histogram' in query.lower():
                    viz = self._create_distribution_plot(df)
                    if viz:
                        visualizations.append(viz)
                
                if 'correlation' in query.lower():
                    viz = self._create_correlation_plot(df)
                    if viz:
                        visualizations.append(viz)
                
                if 'trend' in query.lower() or 'time' in query.lower():
                    viz = self._create_trend_plot(df)
                    if viz:
                        visualizations.append(viz)
                
                # Always try to create a summary visualization if none of the above matched
                if not visualizations and len(df.select_dtypes(include=['number']).columns) > 0:
                    viz = self._create_summary_plot(df)
                    if viz:
                        visualizations.append(viz)
            
            # Create summary data table if response contains tabular data
            if isinstance(response, pd.DataFrame):
                data_tables.append({
                    'title': 'Query Results',
                    'data': response.head(100).to_dict('records'),
                    'columns': list(response.columns)
                })
            
            return {
                'visualizations': visualizations,
                'data_tables': data_tables
            }
            
        except Exception as e:
            logger.error(f"Visualization creation error: {str(e)}")
            return None
    
    def _create_distribution_plot(self, df):
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                return None
            
            col = numeric_cols[0]  # Use first numeric column
            
            fig = px.histogram(df, x=col, title=f'Distribution of {col}')
            return {
                'type': 'plotly',
                'title': f'Distribution of {col}',
                'html': pio.to_html(fig, include_plotlyjs='cdn')
            }
        except:
            return None
    
    def _create_correlation_plot(self, df):
        try:
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.shape[1] < 2:
                return None
            
            corr_matrix = numeric_df.corr()
            fig = px.imshow(corr_matrix, text_auto=True, title='Correlation Matrix')
            
            return {
                'type': 'plotly',
                'title': 'Correlation Matrix',
                'html': pio.to_html(fig, include_plotlyjs='cdn')
            }
        except:
            return None
    
    def _create_trend_plot(self, df):
        try:
            # Look for date columns
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) == 0:
                # Try to find columns that might be dates
                for col in df.columns:
                    if 'date' in col.lower() or 'time' in col.lower():
                        try:
                            df[col] = pd.to_datetime(df[col])
                            date_cols = [col]
                            break
                        except:
                            continue
            
            if len(date_cols) == 0:
                return None
            
            date_col = date_cols[0]
            numeric_cols = df.select_dtypes(include=['number']).columns
            
            if len(numeric_cols) == 0:
                return None
            
            numeric_col = numeric_cols[0]
            
            # Create trend plot
            df_sorted = df.sort_values(date_col)
            fig = px.line(df_sorted, x=date_col, y=numeric_col, 
                         title=f'Trend of {numeric_col} over time')
            
            return {
                'type': 'plotly',
                'title': f'Trend of {numeric_col} over time',
                'html': pio.to_html(fig, include_plotlyjs='cdn')
            }
        except:
            return None
    
    def _create_summary_plot(self, df):
        """Create a summary visualization for the dataset"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) == 0:
                return None
            
            # Take first few numeric columns for a summary plot
            cols_to_plot = numeric_cols[:4]  # Limit to 4 columns for readability
            
            if len(cols_to_plot) == 1:
                # Single numeric column - create histogram
                col = cols_to_plot[0]
                fig = px.histogram(df, x=col, title=f'Distribution of {col}')
            else:
                # Multiple columns - create box plot
                df_melted = df[cols_to_plot].melt(var_name='Column', value_name='Value')
                fig = px.box(df_melted, x='Column', y='Value', title='Data Summary')
            
            return {
                'type': 'plotly',
                'title': 'Data Summary',
                'html': pio.to_html(fig, include_plotlyjs='cdn')
            }
        except:
            return None
    
    def _save_result(self, result_id, result, datasets):
        try:
            result_file = os.path.join(self.results_folder, f"{result_id}.json")
            
            # Save result metadata
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            # Save datasets for export
            for i, df in enumerate(datasets):
                csv_file = os.path.join(self.results_folder, f"{result_id}_dataset_{i}.csv")
                df.to_csv(csv_file, index=False)
                
        except Exception as e:
            logger.error(f"Error saving result: {str(e)}")
    
    def get_query_history(self):
        return sorted(self.history, key=lambda x: x['timestamp'], reverse=True)[:50]  # Last 50 queries
    
    def export_result(self, result_id, export_format='csv'):
        try:
            result_file = os.path.join(self.results_folder, f"{result_id}.json")
            
            if not os.path.exists(result_file):
                return None
            
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            if export_format == 'csv':
                # Find the first dataset CSV
                dataset_file = os.path.join(self.results_folder, f"{result_id}_dataset_0.csv")
                if os.path.exists(dataset_file):
                    return dataset_file
            
            elif export_format == 'json':
                return result_file
            
            return None
            
        except Exception as e:
            logger.error(f"Error exporting result: {str(e)}")
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