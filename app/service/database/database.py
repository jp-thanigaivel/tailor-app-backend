import logging
from datetime import datetime

from bson.objectid import ObjectId
from pymongo import InsertOne
from pymongo.cursor import Cursor
from pymongo.errors import BulkWriteError
from pymongo.results import UpdateResult, DeleteResult
from starlette import status

from app.dependencies.database.mongodb.database import MongoDBClient
from app.observability.app_observability_tracer import start_app_tracing
from app.observability.app_observability_utils import AppTraceSpanEnum
from app.utils.app_constant import RES_C_KEY_PAGINATION, RES_C_KEY_DATA, Q_FILTER_CONDITION_AND, \
    DEFAULT_DB_IS_PRESENT_LIMIT, STATUS_TYPE_ERROR, STATUS_DESC_DATABASE_EXCEPTION, STATUS_DESC_NO_DATA, \
    Q_AGG_TOTAL_COUNT, DEFAULT_DB_PAGE_SIZE
from app.core.exceptions import DataBaseException, NoDataFoundException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.common_functions import CommonUtils
from app.utils.database import get_span_attributes, get_span_name

logger = logging.getLogger(__name__)
db_client = MongoDBClient().get_client()


class MongoDBOperations:

    @classmethod
    def insert_document(cls, db_name, db_coll, document_entity):
        logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll, AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value, attributes=span_attributes) as span:
            logger.info("inserting into db ".format(str(db_coll)))
            db_response = db_collection.insert_one(document_entity.model_dump(exclude_none=True))

            logger.debug("db_response {}".format(str(db_response)))
            logger.debug("db_response.acknowledged {}".format(str(db_response.acknowledged)))

            document_id = db_response.inserted_id
            logger.debug("created document_id {}".format(str(document_id)))
            return document_id

    @classmethod
    def insert_multi_document(cls, document_entities):
        logger.info("inset multiple document")
        db_resp_doc_id = []
        with db_client.start_session() as session:
            with session.start_transaction():
                try:
                    insert_operations = []
                    for document_entity in document_entities:
                        db_name = document_entity['db_name']
                        db_coll = document_entity['db_coll']
                        doc_name = document_entity['doc_name']
                        document_entity = document_entity['document_entity']
                        logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))
                        logger.info("db document_entity {}".format(str(document_entity.model_dump(exclude_none=True))))

                        db_collection = db_client[db_name][db_coll]

                        # Tracing Start
                        span_name = get_span_name(db_name, db_coll,
                                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value)
                        span_attributes = get_span_attributes(db_name, db_coll,
                                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value,
                                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_INSERT.value)
                        with start_app_tracing(span_name=span_name,
                                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                                               attributes=span_attributes) as span:
                            insert_operation = InsertOne(document_entity.model_dump(exclude_none=True))
                            insert_operations.append(insert_operation)

                            db_response = db_collection.insert_one(document_entity.model_dump(exclude_none=True))
                            logger.debug("db_response {}".format(str(db_response)))
                            logger.debug("db_response.acknowledged {}".format(str(db_response.acknowledged)))

                            document_id = db_response.inserted_id
                            logger.debug("created document_id {} | db_coll {} | doc_name {} ".format(str(document_id),
                                                                                                     str(db_coll),
                                                                                                     str(doc_name)))
                            db_resp_doc_id.append({'doc_name': doc_name, 'document_id': document_id})
                            # logger.debug("created bulk document list {}".format(str(document_id)))

                    # bulk_result = db_collection.bulk_write(insert_operations, session=session)
                    # inserted_ids = bulk_result.inserted_ids
                    # acknowledged = bulk_result.acknowledged

                    # logger.info("Inserted IDs: {}".format(inserted_ids))
                    # logger.info("Acknowledgement response: {}".format(acknowledged))
                    session.commit_transaction()
                except BulkWriteError as exp:
                    logger.error("BulkWriteError occurred in insert_multi_document {}".format(str(exp)))
                    session.abort_transaction()
                    logger.error("abort transaction")
                    raise DataBaseException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                            STATUS_DESC_DATABASE_EXCEPTION)
                except Exception as exp:
                    logger.error("Exception occurred in insert_multi_document {}".format(str(exp)))
                    session.abort_transaction()
                    logger.error("abort transaction")
                    raise DataBaseException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                            STATUS_DESC_DATABASE_EXCEPTION)
        return db_resp_doc_id

    @classmethod
    def upsert_document(cls, db_name, db_coll, filter_query, update_query, upsert=True):

        logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        db_collection = db_client[db_name][db_coll]

        """
        array_filters = [
            {"elem.payment_id": "P00046"}  # Update the element with payment_id "P00050"
        ]
        db_response: UpdateResult = db_collection.update_one(filter_query, update_query, upsert, array_filters= array_filters)
        """

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_UPSERT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_UPSERT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_UPSERT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            logger.info("upsert into db {} ".format(str(db_coll)))
            db_response: UpdateResult = db_collection.update_one(filter_query, update_query, upsert)

            logger.debug("db_response {}".format(str(db_response)))
            logger.debug("db_response.acknowledged {}".format(str(db_response.acknowledged)))

            document_id = db_response.upserted_id
            matched_count = db_response.matched_count
            modified_count = db_response.modified_count
            raw_result = db_response.raw_result
            logger.debug("upsert document_id {} | matched_count {} | "
                         "modified_count {} | raw_result {}".format(str(document_id), str(matched_count),
                                                                    str(modified_count), str(raw_result)))
            if matched_count > 0 and modified_count > 0:
                return modified_count
            else:
                logger.error("No data updated in database filter_query {}".format(str(filter_query)))
                raise NoDataFoundException(status.HTTP_404_NOT_FOUND, STATUS_TYPE_ERROR,
                                           STATUS_DESC_NO_DATA + " while update db_coll:" + str(db_coll))

    @classmethod
    def find_document_with_pagination(cls, db_name, db_coll, filter_condition: list = None,
                                      page_size: int = DEFAULT_DB_PAGE_SIZE, page_number: int = None, cursor: str = None,
                                      sort_condition=None, is_backward: bool = False):
        logger.info("In find_document_with_pagination db_name {} ".format(str(db_name), ))

        if page_size is None:
            page_size = DEFAULT_DB_PAGE_SIZE
        if sort_condition is None:
            sort_condition = [("updatedOn", -1), ("_id", -1)]

        # Keep a copy of original sort keys for cursor generation
        original_sort_condition = sort_condition

        # For backward navigation, reverse the sort order
        if is_backward:
             new_sort_condition = []
             for key, direction in sort_condition:
                 new_sort_condition.append((key, -direction))
             sort_condition = new_sort_condition
        
        limit = page_size + 1
        total_count = None
        cursor_filter_condition = {}
        if cursor:
            logger.info("received cursor in request {} ".format(str(cursor)))
            decoded_cursor = CommonUtils.decode_string(cursor)
            last_doc_detail = CommonUtils.get_json_format(decoded_cursor)

            or_conditions = []
            previous_equalities = {}

            # Iterate through sort keys to build the OR clauses
            for key, direction in sort_condition:
                val = last_doc_detail.get(key)
                
                # Handling ObjectId conversion for _id if needed
                if key == "_id" and isinstance(val, str):
                     val = ObjectId(val)
                     
                op = "$lt" if direction == -1 else "$gt"
                
                # Clause: (Key1 == Val1) AND ... AND (KeyN {op} ValN)
                clause = previous_equalities.copy()
                clause[key] = {op: val}
                
                or_conditions.append(clause)
                
                # Add current key to equalities for next clauses
                previous_equalities[key] = val
                
            if or_conditions:
                 cursor_filter_condition["$or"] = or_conditions
            
        query = {Q_FILTER_CONDITION_AND: [filter_condition, cursor_filter_condition]}
        logger.info("before querying db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        logger.debug("query {}".format(str(query)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            db_cursor: Cursor = db_collection \
                .find(query) \
                .sort(sort_condition) \
                .limit(limit)

            # Override default behavior if limit-based is requested
            if page_number and cursor is None:
                db_cursor = db_cursor.skip(((page_number - 1) * page_size) if page_number > 0 else 0).limit(page_size)

            db_document = list(db_cursor)
            
            # If backward navigation, reverse results to correct order
            if is_backward:
                db_document.reverse()
                
            document_count = len(db_document)
            previous_cursor = None
            next_cursor = None

            logger.info("after querying count {} page_size {}".format(str(document_count), str(page_size)))

            # Check next page for cursor based
            has_next = document_count > page_size
            if has_next:
                logger.info("has next page ")
                document_count = document_count - 1
                if is_backward:
                     # If backward, and we found extra items, the "extra" is at the BEGINNING of valid range (before reverse)
                     # After reverse, it becomes the first item
                     db_document = db_document[1:]
                else:
                     db_document = db_document[:-1]

            # Generate cursors based on updated document list
            if len(db_document) > 0:
                first_document = db_document[0]
                last_document = db_document[-1]
                
                def generate_cursor_str(doc):
                    cursor_data = {}
                    for k, _ in original_sort_condition:
                        v = doc.get(k)
                        if k == "_id":
                             v = str(v)
                        cursor_data[k] = v
                    return CommonUtils.encode_string(cursor_data)
                
                prev_cursor_str = generate_cursor_str(first_document)
                next_cursor_str = generate_cursor_str(last_document)

                if is_backward:
                    # In backward navigation:
                    # We have a prev page (older items) if has_next (we found items beyond the ones we show)
                    if has_next:
                        previous_cursor = prev_cursor_str
                        logger.info("encoded previous cursor (backward nav) {}".format(str(previous_cursor)))
                    
                    # We definitely have a next page (where we came from) if we had a cursor, 
                    # unless we are at the very end?? 
                    # Standard logic: if we have a cursor, we assume we can go back to it?
                    if cursor:
                        next_cursor = next_cursor_str
                        logger.info("encoded next cursor (backward nav) {}".format(str(next_cursor)))
                else:
                    if has_next:
                        next_cursor = next_cursor_str
                        logger.info("encoded next cursor (forward nav) {}".format(str(next_cursor)))
                    
                    if cursor:
                        previous_cursor = prev_cursor_str
                        logger.info("encoded previous cursor (forward nav) {}".format(str(previous_cursor)))

            # Check total count for limit based only for first time
            if page_number and (page_number - 1) == 0:
                logger.info("Fetching total_count for limit based pagination")
                total_count_pipeline = CommonUtils.get_agg_pipeline_total_count(filter_condition)
                db_collection_count = db_client[db_name][db_coll]
                result = list(db_collection_count.aggregate(total_count_pipeline))
                total_count = result[0][Q_AGG_TOTAL_COUNT] if result else 0
                logger.info("Fetched total_count {}".format(str(total_count)))

            pagination_object = AppObjectMapper.get_pagination_obj(count=document_count, previous_page=previous_cursor,
                                                                   next_page=next_cursor, total_count=total_count)

            return {
                RES_C_KEY_DATA: list(db_document),
                RES_C_KEY_PAGINATION: pagination_object
            }

    @classmethod
    def find_one_document(cls, db_name, db_coll, query):
        logger.info("In find_one_document db_name {} ".format(str(db_name)))

        logger.info("before querying db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        logger.debug("query {}".format(str(query)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            db_cursor: Cursor = db_collection.find_one(query)

            db_document = list(db_cursor)
            document_count = len(db_document)

            logger.info("after querying count {}".format(str(document_count)))
            return {
                RES_C_KEY_DATA: list(db_document)
            }

    @classmethod
    def find_document(cls, db_name, db_coll, filter_condition: dict = None,
                      page_size: int = None, page_number: int = None,
                      sort_condition=None):
        logger.info("In find_document db_name {} ".format(str(db_name), ))
        query = filter_condition
        logger.info("before querying db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        logger.debug("query {}".format(str(query)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            db_cursor: Cursor = db_collection \
                .find(query)

            if sort_condition:
                db_cursor.sort(sort_condition)

            if page_number and page_size:
                db_cursor = db_cursor.skip(((page_number - 1) * page_size) if page_number > 0 else 0).limit(page_size)

            db_document = list(db_cursor)
            document_count = len(db_document)
            logger.info("after querying count {} page_size {}".format(str(document_count), str(page_size)))

            return {
                RES_C_KEY_DATA: list(db_document)
            }

    @classmethod
    def is_document_present(cls, db_name, db_coll, query):
        logger.info("In is_document_present db_name {} ".format(str(db_name)))

        logger.info("before querying db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        logger.debug("query {}".format(str(query)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_SELECT.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            db_cursor: Cursor = db_collection.count_documents(query, limit=DEFAULT_DB_IS_PRESENT_LIMIT)
            logger.info("after querying count {}".format(str(db_cursor)))
            if db_cursor:
                return True
            else:
                return False

    @classmethod
    def replace_document(cls, db_name, db_coll, filter_condition, document_entity):
        logger.info("get db client with db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_REPLACE.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_REPLACE.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_REPLACE.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            logger.info("replace into db {} ".format(str(db_coll)))
            db_response = db_collection.replace_one(filter_condition, document_entity.model_dump(exclude_none=True))

            logger.debug("db_response {}".format(str(db_response)))
            logger.debug("db_response modified_count {}".format(str(db_response.modified_count)))
            logger.debug("db_response upserted_id {}".format(str(db_response.upserted_id)))
            logger.debug("db_response raw_result {}".format(str(db_response.raw_result)))
            document_id = None
            if db_response.modified_count > 0:
                document_id = db_response.upserted_id
            elif db_response.upserted_id:
                document_id = db_response.upserted_id
            else:
                raise DataBaseException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                        STATUS_DESC_DATABASE_EXCEPTION + " No Document replaced")

            logger.debug("replace document_id {}".format(str(document_id)))
            return document_id

    @classmethod
    def delete_document(cls, db_name, db_coll, query):
        logger.info("In delete_document db_name {} ".format(str(db_name)))

        logger.info("before deleting db_name {} db_coll {}".format(str(db_name), str(db_coll)))
        logger.debug("query {}".format(str(query)))
        db_collection = db_client[db_name][db_coll]

        # Tracing Start
        span_name = get_span_name(db_name, db_coll,
                                  AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_DELETE.value)
        span_attributes = get_span_attributes(db_name, db_coll,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_DELETE.value,
                                              AppTraceSpanEnum.SPAN_NAME_DB_OPERATION_DELETE.value)
        with start_app_tracing(span_name=span_name,
                               span_kind=AppTraceSpanEnum.SPAN_KIND_DB.value,
                               attributes=span_attributes) as span:
            db_response: DeleteResult = db_collection.delete_one(query, )

            logger.info("after delete document count {}".format(str(db_response.deleted_count)))
            logger.info("after delete document acknowledged {}".format(str(db_response.acknowledged)))
            logger.debug("after delete document raw_result {}".format(str(db_response.raw_result)))
            if db_response.deleted_count > 0:
                logger.info("Document deleted for criteria {}".format(str(query)))

            """
            Client can decide what to do
            else:
                raise DataBaseException(status.HTTP_500_INTERNAL_SERVER_ERROR, STATUS_TYPE_ERROR,
                                        STATUS_DESC_DATABASE_EXCEPTION + " No Document deleted")
            """
            return db_response.deleted_count
