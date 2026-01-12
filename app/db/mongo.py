import logging
import pathlib

from pymongo import MongoClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    _client: MongoClient = None

    @classmethod
    def initialize(cls):
        if cls._client is None:
            a = pathlib.Path(__file__).resolve().parent.parent.parent
            logger.info("Initializing MongoDB Client "+a.parent.as_posix())

            cls._client = MongoClient(settings.db_url)
            # Verify connection
            cls._client.admin.command('ping')
            logger.info("MongoDB connection successful")
    
    @classmethod
    def get_client(cls) -> MongoClient:
        if cls._client is None:
            cls.initialize()
        return cls._client

    @classmethod
    def get_db(cls):
        return cls.get_client()[settings.data_base]

    @classmethod
    def close(cls):
        if cls._client:
            logger.info("Closing MongoDB Client")
            cls._client.close()
            cls._client = None
