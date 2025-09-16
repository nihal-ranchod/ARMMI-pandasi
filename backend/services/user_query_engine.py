import pandas as pd
import os
import uuid
from datetime import datetime, timezone
from pandasai import Agent
from pandasai.llm import OpenAI
import logging

logger = logging.getLogger(__name__)

class UserQueryEngine:
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

        if not self.openai_api_key:
            logger.warning("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")

    def execute_query(self, query_text, user, shared_data_processor=None):
        """Execute query using PandasAI only"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.")

        result_id = str(uuid.uuid4())

        try:
            # Load datasets
            if shared_data_processor:
                datasets_dict = shared_data_processor.load_all_shared_datasets()
                datasets = list(datasets_dict.values())
                dataset_names = list(datasets_dict.keys())
            else:
                datasets = []
                dataset_names = []

                # Load user datasets (fallback)
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

            logger.info(f"Loaded {len(datasets)} datasets: {dataset_names}")

            # Initialize PandasAI Agent with minimal configuration
            llm = OpenAI(api_token=self.openai_api_key)

            # Create agent with config that works better with output validation
            config = {
                "llm": llm,
                "verbose": False,
                "enable_cache": False,  # Disable cache to avoid cached broken responses
                "save_charts": False,   # Disable automatic chart saving to avoid format conflicts
            }

            agent = Agent(datasets, config=config)

            # Execute query
            logger.info(f"Executing query: {query_text}")
            response = agent.chat(query_text)

            logger.info(f"PandasAI response: {response}")
            logger.info(f"Response type: {type(response)}")

            # Create result structure
            result = {
                'id': result_id,
                'query': query_text,
                'datasets_used': dataset_names,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'response_type': 'text',
                'response': str(response),
                'visualizations': [],
                'data_tables': [],
                'success': True
            }

            # Check if response is a chart path
            if isinstance(response, str) and response.endswith('.png') and '/charts/' in response:
                logger.info(f"Detected chart response: {response}")

                # Encode chart to base64 for frontend display
                chart_data = self._encode_chart_to_base64(response)
                if chart_data:
                    chart_id = str(uuid.uuid4())
                    result['visualizations'].append({
                        'type': 'chart',
                        'title': 'Generated Chart',
                        'id': chart_id,
                        'data': chart_data,
                        'url': f'/api/charts/{chart_id}'
                    })
                    result['response_type'] = 'chart'
                    # Don't show the file path, just indicate a chart was generated
                    result['response'] = 'Chart generated successfully'
                    logger.info(f"Added chart visualization with ID: {chart_id}")

            # Add to user's query history
            query_info = {
                'query': query_text,
                'datasets_used': dataset_names,
                'success': True,
                'timestamp': result['timestamp'],
                'result_summary': str(response)[:500],
                'full_result': result
            }

            query_id = user.add_query_to_history(query_info)
            if query_id:
                result['query_id'] = query_id
                query_info['query_id'] = query_id

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Query execution error: {error_msg}")

            # Add failed query to user history
            timestamp = datetime.now(timezone.utc).isoformat()
            query_info = {
                'query': query_text,
                'datasets_used': dataset_names if 'dataset_names' in locals() else [],
                'success': False,
                'timestamp': timestamp,
                'error': error_msg
            }

            user.add_query_to_history(query_info)

            # Create error response
            error_result = {
                'id': str(uuid.uuid4()),
                'query': query_text,
                'datasets_used': dataset_names if 'dataset_names' in locals() else [],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'response_type': 'error',
                'response': f"Error: {error_msg}",
                'visualizations': [],
                'data_tables': [],
                'success': False,
                'error': error_msg
            }

            return error_result

    def get_query_history(self, user):
        """Get query history for a user"""
        try:
            logger.info(f"Getting query history for user {user.email}")
            logger.info(f"Raw query history count: {len(user.query_history)}")

            # Debug: Print first few items
            if user.query_history:
                for i, item in enumerate(user.query_history[:3]):
                    logger.info(f"History item {i}: {item}")

            # Sort by timestamp (newest first) and limit to 50 queries
            sorted_history = sorted(
                user.query_history,
                key=lambda x: x.get('timestamp', ''),
                reverse=True
            )[:50]

            formatted_history = []
            for item in sorted_history:
                formatted_item = {
                    'id': item.get('query_id') or item.get('id', str(uuid.uuid4())),
                    'query': item.get('query', ''),
                    'datasets_used': item.get('datasets_used', []),
                    'datasets': item.get('datasets_used', []),  # Frontend expects 'datasets'
                    'success': item.get('success', False),
                    'timestamp': item.get('timestamp').isoformat() if hasattr(item.get('timestamp'), 'isoformat') else item.get('timestamp', datetime.now(timezone.utc).isoformat()),
                    'result_summary': item.get('result_summary', 'No summary available')
                }

                if not item.get('success', False):
                    formatted_item['error'] = item.get('error', 'Unknown error')

                formatted_history.append(formatted_item)

            logger.info(f"Retrieved {len(formatted_history)} history items for user {user.email}")
            return formatted_history

        except Exception as e:
            logger.error(f"Error retrieving query history for user {user.email}: {str(e)}")
            return []

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

    def get_query_result(self, query_id, user):
        """Get a specific query result by ID"""
        try:
            for query in user.query_history:
                if query.get('query_id') == query_id and 'full_result' in query:
                    return query['full_result']
            return None
        except Exception as e:
            logger.error(f"Error getting query result {query_id}: {str(e)}")
            return None

    def _encode_chart_to_base64(self, chart_path):
        """Encode chart file to base64 for frontend display"""
        try:
            import os
            import base64

            if os.path.exists(chart_path):
                with open(chart_path, 'rb') as chart_file:
                    encoded_string = base64.b64encode(chart_file.read()).decode()

                # Clean up the file after encoding
                os.remove(chart_path)
                logger.info(f"Encoded and removed chart file: {chart_path}")

                return encoded_string
            else:
                logger.warning(f"Chart file not found: {chart_path}")
                return None

        except Exception as e:
            logger.error(f"Error encoding chart to base64: {str(e)}")
            return None