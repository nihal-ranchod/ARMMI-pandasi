import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

class MongoDB:
    _instance = None
    _client = None
    _database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.connect()
    
    def connect(self):
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb+srv://nihalranchod_db_user:U1UmClr8Allz308p@ammina.wwxrxig.mongodb.net/?retryWrites=true&w=majority&appName=AMMINA')
            
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test the connection
            self._client.admin.command('ping')
            
            # Get database name from URI or use default
            db_name = os.getenv('MONGODB_DB_NAME', 'ammina_platform')
            self._database = self._client[db_name]
            
            # Get server info for logging
            server_info = self._client.server_info()
            logger.info(f"Successfully connected to MongoDB")
            logger.info(f"Database: {db_name}")
            logger.info(f"MongoDB Version: {server_info.get('version', 'Unknown')}")
            logger.info(f"Connection URI: {mongodb_uri.split('@')[1] if '@' in mongodb_uri else 'localhost'}")  # Don't log credentials
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            raise
    
    @property
    def client(self):
        if self._client is None:
            self.connect()
        return self._client
    
    @property
    def db(self):
        if self._database is None:
            self.connect()
        return self._database
    
    def get_collection(self, collection_name):
        return self.db[collection_name]
    
    @property
    def users(self):
        return self.db['users']
    
    @property
    def dataset_data(self):
        return self.db['dataset_data']
    
    def close_connection(self):
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

# Singleton instance
mongodb = MongoDB()