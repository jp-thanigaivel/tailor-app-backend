import threading

from pymongo import MongoClient

from app.core.config import settings


class MongoDBClient:
    _instance = None
    _is_initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._is_initialized:
            with cls._lock:
                if not cls._is_initialized:
                    cls._instance = super().__new__(cls)
                    cls._is_initialized = True
        return cls._instance

    def __init__(self):
        self.client = MongoClient(settings.db_url)
        self.db = self.client[settings.data_base]

    def get_client(self):
        return self.client
