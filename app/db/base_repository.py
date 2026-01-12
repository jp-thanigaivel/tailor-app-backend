from typing import TypeVar, Generic, List, Optional, Any, Dict, Type, Union
from pydantic import BaseModel
from pymongo.collection import Collection
from bson import ObjectId
from app.db.mongo import MongoDBManager
from app.db.filters import build_tenant_filter
from app.core.dependencies import TenantContext
from app.core.telemetry import start_span
from opentelemetry.trace import SpanKind
import logging

logger = logging.getLogger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)

class CRUDBase(Generic[TModel]):
    def __init__(self, model: Type[TModel], collection_name: str):
        self.model = model
        self.collection_name = collection_name

    @property
    def collection(self) -> Collection:
        return MongoDBManager.get_db()[self.collection_name]

    def _serialize_doc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data and "_id" in data:
            data["_id"] = str(data["_id"])
            data["id"] = data["_id"]
        return data

    def create(self, context: TenantContext, obj_in: Dict[str, Any]) -> TModel:
        with start_span(f"db.{self.collection_name}.create", kind=SpanKind.CLIENT) as span:
            # Inject tenant context
            obj_in["org_id"] = context.org_id
            obj_in["business_unit_id"] = context.business_unit_id
            if context.owner_id:
                 obj_in["owner_id"] = context.owner_id
            
            result = self.collection.insert_one(obj_in)
            obj_in["_id"] = result.inserted_id
            return self.model(**self._serialize_doc(obj_in))

    def get(self, context: TenantContext, filter_query: Dict[str, Any]) -> Optional[TModel]:
        with start_span(f"db.{self.collection_name}.get", kind=SpanKind.CLIENT) as span:
            query = build_tenant_filter(context, filter_query)
            data = self.collection.find_one(query)
            if data:
                return self.model(**self._serialize_doc(data))
            return None

    def get_by_id(self, context: TenantContext, id: Union[str, ObjectId]) -> Optional[TModel]:
        _id = ObjectId(id) if isinstance(id, str) and ObjectId.is_valid(id) else id
        return self.get(context, {"_id": _id})

    def get_all(self, context: TenantContext, filter_query: Dict[str, Any] = None, skip: int = 0, limit: int = 100) -> List[TModel]:
        with start_span(f"db.{self.collection_name}.get_all", kind=SpanKind.CLIENT) as span:
            query = build_tenant_filter(context, filter_query)
            cursor = self.collection.find(query).skip(skip).limit(limit)
            return [self.model(**self._serialize_doc(doc)) for doc in cursor]

    def get_all_with_pagination(
        self, 
        context: TenantContext, 
        filter_query: Dict[str, Any] = None, 
        page_size: int = 10, 
        page_number: int = None, 
        cursor: str = None,
        sort_condition: List = None,
        is_backward: bool = False
    ) -> Dict[str, Any]:
        with start_span(f"db.{self.collection_name}.get_all_with_pagination", kind=SpanKind.CLIENT) as span:
            logger.info(f"Pagination filter_query: {filter_query}")
            query = build_tenant_filter(context, filter_query)
            logger.info(f"Pagination Query: {query}")
            from app.service.database.database import MongoDBOperations
            from app.utils.app_constant import RES_C_KEY_DATA, RES_C_KEY_PAGINATION
            from app.core.config import settings
            
            db_response = MongoDBOperations.find_document_with_pagination(
                db_name=settings.data_base,
                db_coll=self.collection_name,
                filter_condition=query,
                page_size=page_size,
                page_number=page_number,
                cursor=cursor,
                sort_condition=sort_condition,
                is_backward=is_backward
            )
            
            docs = db_response[RES_C_KEY_DATA]
            pagination = db_response[RES_C_KEY_PAGINATION]
            
            return {
                "data": [self.model(**self._serialize_doc(doc)) for doc in docs],
                "pagination": pagination
            }

    def update(self, context: TenantContext, filter_query: Dict[str, Any], obj_in: Dict[str, Any]) -> Optional[TModel]:
        with start_span(f"db.{self.collection_name}.update", kind=SpanKind.CLIENT) as span:
            query = build_tenant_filter(context, filter_query)
            from pymongo import ReturnDocument
            result = self.collection.find_one_and_update(
                query,
                {"$set": obj_in},
                return_document=ReturnDocument.AFTER
            )
            if result:
                return self.model(**self._serialize_doc(result))
            return None

    def delete(self, context: TenantContext, filter_query: Dict[str, Any]) -> bool:
        with start_span(f"db.{self.collection_name}.delete", kind=SpanKind.CLIENT) as span:
            query = build_tenant_filter(context, filter_query)
            result = self.collection.delete_one(query)
            return result.deleted_count > 0

    def count(self, context: TenantContext, filter_query: Dict[str, Any] = None) -> int:
        with start_span(f"db.{self.collection_name}.count", kind=SpanKind.CLIENT) as span:
            query = build_tenant_filter(context, filter_query)
            return self.collection.count_documents(query)
