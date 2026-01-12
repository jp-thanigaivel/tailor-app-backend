
import json
import base64

# Mocking the dependencies
DEFAULT_DB_PAGE_SIZE = 2
RES_C_KEY_DATA = "data"
RES_C_KEY_PAGINATION = "paginationInfo"
Q_FILTER_CONDITION_AND = "$and"
Q_AGG_TOTAL_COUNT = "total_count"

# Mock logger
class Logger:
    def info(self, msg): pass
    def debug(self, msg): pass
    def warning(self, msg): pass

logger = Logger()
db_client = None # Mock client placeholder

# Mock ObjectId
class ObjectId:
    def __init__(self, id_val):
        self.id_val = str(id_val)
    
    def __str__(self):
        return self.id_val
        
    def __repr__(self):
        return f"ObjectId('{self.id_val}')"
        
    def __eq__(self, other):
        return str(self) == str(other)
        
    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)

# Mock CommonUtils
class CommonUtils:
    @staticmethod
    def decode_string(input_encoded_data):
        return base64.b64decode(input_encoded_data).decode("utf-8")

    @staticmethod
    def encode_string(input_data):
        return base64.b64encode(json.dumps(input_data).encode("utf-8")).decode("utf-8")

    @staticmethod
    def get_json_format(input_data):
        return json.loads(input_data)
        
    @staticmethod
    def get_agg_pipeline_total_count(filter_condition):
        return []

class AppObjectMapper:
    @staticmethod
    def get_pagination_obj(count, previous_page, next_page, total_count=None):
        return {
            "count": count,
            "previousPage": previous_page,
            "nextPage": next_page,
            "totalCount": total_count
        }

# Mock Tracing
class MockSpan:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass

def start_app_tracing(**kwargs):
    return MockSpan()

def get_span_name(*args): return ""
def get_span_attributes(*args): return {}

class AppTraceSpanEnum:
    SPAN_KIND_DB = "db"
    SPAN_NAME_DB_OPERATION_SELECT = "select"

# Mock DB Collection/Cursor
class MockCursor:
    def __init__(self, data):
        self.data = data
        self._skip = 0
        self._limit = 0
    
    def sort(self, sort_condition):
        # We do recursive sort or multisort
        # Python's list.sort is stable, so we can reverse iterate keys
        for field, direction in reversed(sort_condition):
            self.data.sort(key=lambda x: str(x.get(field)) if x.get(field) is not None else "", reverse=(direction == -1))
        
        return self

    def limit(self, n):
        self._limit = n
        return self
        
    def skip(self, n):
        self._skip = n
        return self

    def __iter__(self):
        res = self.data[self._skip : self._skip + self._limit] if self._limit > 0 else self.data[self._skip:]
        return iter(res)
    
class MockCollection:
    def __init__(self, data):
        self.data = data
    
    def find(self, query):
        filtered_data = []
        and_conditions = query.get(Q_FILTER_CONDITION_AND, [])
        if isinstance(and_conditions, tuple): # Handle tuple bug in mock if any
            and_conditions = list(and_conditions)
            
        # Support single list or nested list structure?
        # My code produces: {Q_FILTER_CONDITION_AND: [filter_condition (list), cursor_filter_condition (dict)]}
        # Wait, filter_condition arg is list?
        # Code: `query = {Q_FILTER_CONDITION_AND: [filter_condition, cursor_filter_condition]}`
        # If filter_condition is None, list contains [None, {}].
        
        # Flatten logic for Mock
        final_conditions = []
        if isinstance(and_conditions, list):
            for item in and_conditions:
                 if isinstance(item, list):
                     final_conditions.extend(item)
                 elif isinstance(item, dict) and item:
                     final_conditions.append(item)
        
        for item in self.data:
            match = True
            for condition in final_conditions:
                if not condition: continue 
                
                if "$or" in condition:
                    or_params = condition["$or"]
                    or_match = False
                    for sub_cond in or_params:
                         if self._matches(item, sub_cond):
                             or_match = True
                             break
                    if not or_match:
                        match = False
                        break
                else:
                    if not self._matches(item, condition):
                        match = False
                        break
            
            if match:
                filtered_data.append(item)
                
        return MockCursor(filtered_data)
    
    def _matches(self, item, condition):
        for field, criteria in condition.items():
            item_val = item.get(field)
            if isinstance(criteria, dict):
                for op, val in criteria.items():
                    val_cmp = str(val)
                    item_cmp = str(item_val) if item_val is not None else ""
                    
                    if op == "$eq":
                        if item_cmp != val_cmp: return False
                    elif op == "$gt":
                         if not (item_cmp > val_cmp): return False
                    elif op == "$lt":
                         if not (item_cmp < val_cmp): return False
            else:
                if str(item_val) != str(criteria): return False
        return True

    def aggregate(self, pipeline):
        return [{"total_count": len(self.data)}]


# The Function Under Test
# We will import the actual file content technically, but since it relies on modules, 
# I will copy paste the FIXED function logic here to verify IT works against the logic I implemented.
# OR I can try to import the file if I mock the imports.
# Mocks are above. I will rewrite the class using the Logic I JUST WROTE.

class MongoDBOperations:
    @classmethod
    def find_document_with_pagination(cls, db_collection, db_name, db_coll, filter_condition: list = None,
                                      page_size: int = DEFAULT_DB_PAGE_SIZE, page_number: int = None, cursor: str = None,
                                      sort_condition=None, is_backward: bool = False):
        
        # Mock adapter: db_collection passed as client for mock simplicity
        
        if page_size is None:
            page_size = DEFAULT_DB_PAGE_SIZE
        if sort_condition is None:
            sort_condition = [("updatedOn", -1), ("_id", -1)]

        original_sort_condition = sort_condition

        if is_backward:
             new_sort_condition = []
             for key, direction in sort_condition:
                 new_sort_condition.append((key, -direction))
             sort_condition = new_sort_condition
        
        limit = page_size + 1
        total_count = None
        cursor_filter_condition = {}
        if cursor:
            # logger.info("received cursor in request {} ".format(str(cursor)))
            decoded_cursor = CommonUtils.decode_string(cursor)
            last_doc_detail = CommonUtils.get_json_format(decoded_cursor)

            or_conditions = []
            previous_equalities = {}

            for key, direction in sort_condition:
                val = last_doc_detail.get(key)
                
                if key == "_id" and isinstance(val, str):
                     val = ObjectId(val)
                     
                op = "$lt" if direction == -1 else "$gt"
                
                clause = previous_equalities.copy()
                clause[key] = {op: val}
                
                or_conditions.append(clause)
                previous_equalities[key] = val
                
            if or_conditions:
                 cursor_filter_condition["$or"] = or_conditions
            
        # Mock Query Structure
        query = {Q_FILTER_CONDITION_AND: [filter_condition, cursor_filter_condition]}
        
        # db_collection = db_client[db_name][db_coll]
        # Use passed mock collection
        
        db_cursor = db_collection \
            .find(query) \
            .sort(sort_condition) \
            .limit(limit)

        if page_number and cursor is None:
            db_cursor = db_cursor.skip(((page_number - 1) * page_size) if page_number > 0 else 0).limit(page_size)

        db_document = list(db_cursor)
        
        if is_backward:
            db_document.reverse()
            
        document_count = len(db_document)
        previous_cursor = None
        next_cursor = None

        has_next = document_count > page_size
        if has_next:
            document_count = document_count - 1
            if is_backward:
                 db_document = db_document[1:]
            else:
                 db_document = db_document[:-1]

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
                if has_next:
                    previous_cursor = prev_cursor_str
                
                if cursor:
                    next_cursor = next_cursor_str
            else:
                if has_next:
                    next_cursor = next_cursor_str
                
                if cursor:
                    previous_cursor = prev_cursor_str

        pagination_object = AppObjectMapper.get_pagination_obj(count=document_count, previous_page=previous_cursor,
                                                               next_page=next_cursor, total_count=total_count)

        return {
            RES_C_KEY_DATA: list(db_document),
            RES_C_KEY_PAGINATION: pagination_object
        }

# Data Setup
data = [
    {"_id": str(i), "val": 10, "extra": "A"} for i in range(1, 6)
]
# Data: 
# 5: 10, A
# 4: 10, A
# 3: 10, A
# 2: 10, A
# 1: 10, A
# Sorted DESC by default ID logic in Mock if data inserted that way? 
# Mock data is list.

mock_collection = MockCollection(data)

# Case 1: 3 Sort Keys, Forward
# Sort: val ASC, extra ASC, _id DESC
# Expected order: 5, 4, 3, 2, 1 

sort_cond = [("val", 1), ("extra", 1), ("_id", -1)]

print(f"Total items: {len(data)}")
print(f"Sort Condition: {sort_cond}")

print("--- Test Forward ---")
# Page 1
res1 = MongoDBOperations.find_document_with_pagination(
    mock_collection, "db", "col", {}, page_size=2, sort_condition=sort_cond
)

print("Page 1:")
for item in res1["data"]:
    print(item)
# Should be 5, 4.

next_cur = res1["paginationInfo"]["nextPage"]
print(f"Next Cursor: {next_cur}")

if next_cur:
    # Page 2
    res2 = MongoDBOperations.find_document_with_pagination(
        mock_collection, "db", "col", {}, page_size=2, cursor=next_cur, sort_condition=sort_cond
    )
    print("Page 2:")
    for item in res2["data"]:
        print(item)
    # Should be 3, 2.
    
    next_cur_2 = res2["paginationInfo"]["nextPage"]
    print(f"Next Cursor 2: {next_cur_2}")
    
    prev_cur_2 = res2["paginationInfo"]["previousPage"]
    print(f"Prev Cursor 2 (Should exist): {prev_cur_2}")
    
    if prev_cur_2:
        print("--- Test Backward ---")
        # Go Backward from Page 2. Should get Page 1 (5, 4).
        res_back = MongoDBOperations.find_document_with_pagination(
            mock_collection, "db", "col", {}, page_size=2, cursor=prev_cur_2, sort_condition=sort_cond, is_backward=True
        )
        print("Page 1 (via Backward):")
        for item in res_back["data"]:
             print(item)
        # Should be 5, 4.
        
        next_cur_back = res_back["paginationInfo"]["nextPage"] # Should point to Page 2
        print(f"Next Cursor (from Backward Page 1): {next_cur_back}")

