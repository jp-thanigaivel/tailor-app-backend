import threading

class MDC:
    _storage = threading.local()

    @classmethod
    def _get_context(cls):
        if not hasattr(cls._storage, 'context'):
            cls._storage.context = {}
        return cls._storage.context

    @classmethod
    def put(cls, key: str, value: str):
        cls._get_context()[key] = value

    @classmethod
    def get(cls, key: str):
        return cls._get_context().get(key)

    @classmethod
    def clear(cls):
        if hasattr(cls._storage, 'context'):
            cls._storage.context.clear()
