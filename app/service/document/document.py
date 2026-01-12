import ast
import logging

from starlette import status

import pandas as pd
from app.core.config import settings as app_config
from app.common.models import TokenData, DBPaginationMeta
from app.service.database.database import MongoDBOperations
from app.utils.app_constant import RES_C_KEY_DATA, RES_C_KEY_PAGINATION, STATUS_TYPE_WARN, STATUS_DESC_NO_DATA, \
    COLL_TODO_MARKETING, COLL_TODO_PRODUCTION, COLL_TODO_DELIVERY
from app.core.exceptions import NoDataFoundException
from app.utils.app_obj_mapper import AppObjectMapper
from app.utils.delivery_constant import Q_ALLOWED_SORT_FIELDS_delivery, Q_ALLOWED_FILTER_FIELDS_delivery
from app.utils.marketing_constant import Q_ALLOWED_FILTER_FIELDS_marketing, Q_ALLOWED_SORT_FIELDS_marketing
from app.utils.production_constant import Q_ALLOWED_FILTER_FIELDS_production, Q_ALLOWED_SORT_FIELDS_production

logger = logging.getLogger(__name__)




def get_dataframe_by_document_name_and_query(query_param: dict[str, str], document_name: str, token_data: TokenData) -> pd.DataFrame:
    logger.info("start processing get_all_marketing")

    db_name = app_config.data_base
    db_coll: str = get_collection_name(document_name)
    db_pagination_metadata: DBPaginationMeta = AppObjectMapper.get_db_meta(query_param,
                                                                           get_allowed_filter_condition(document_name),
                                                                           get_allowed_sort_condition(document_name))

    logger.info(
        "get db client with db_name {} db_coll {} filter_condition {} sort_key {}".format(str(db_name), str(db_coll),
                                                                                          str(db_pagination_metadata.filter_condition),
                                                                                          str(db_pagination_metadata.sort_key)))
    db_response = MongoDBOperations.find_document(db_name=db_name, db_coll=db_coll,
                                                  filter_condition=db_pagination_metadata.filter_condition,
                                                  page_size=db_pagination_metadata.page_number,
                                                  page_number=db_pagination_metadata.page_number)
    db_document = db_response[RES_C_KEY_DATA]
    logger.debug("Received response from db data {} ".format(str(db_document)))

    if db_document and len(db_document) > 0:
        df = pd.DataFrame(db_document)
        df = df.drop(columns=["_id"])
        df = flatten_json_document(df, document_name)
        return df
    else:
        logger.warning("No marketing found")
        raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA)

def get_allowed_filter_condition(document_name: str) -> dict[str, dict[str, str]]:
    match document_name:
        case "marketing":
            return Q_ALLOWED_FILTER_FIELDS_marketing
        case "production":
            return Q_ALLOWED_FILTER_FIELDS_production
        case "delivery":
            return Q_ALLOWED_FILTER_FIELDS_delivery
        case _:
            raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " document_name: " + str(document_name))

def get_allowed_sort_condition(document_name: str) -> dict[str, dict[str, str]]:
    match document_name:
        case "marketing":
            return Q_ALLOWED_SORT_FIELDS_marketing
        case "production":
            return Q_ALLOWED_SORT_FIELDS_production
        case "delivery":
            return Q_ALLOWED_SORT_FIELDS_delivery
        case _:
            raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " document_name: " + str(document_name))

def get_collection_name(document_name: str) -> str:
    match document_name:
        case "marketing":
            return COLL_TODO_MARKETING
        case "production":
            return COLL_TODO_PRODUCTION
        case "delivery":
            return COLL_TODO_DELIVERY
        case _:
            raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                   STATUS_DESC_NO_DATA + " document_name: " + str(document_name))

def flatten_json_document(df: pd.DataFrame,  document_name: str) -> pd.DataFrame:
    match document_name:
        case "marketing":
            df: pd.DataFrame = flatten_json_by_column(df, "qty")
            df: pd.DataFrame = flatten_json_by_column(df, "unit_price")
            df: pd.DataFrame = flatten_json_by_column(df, "contact_phone_number")
            return df
        case "production":
            return df
        case "delivery":
            df: pd.DataFrame = flatten_json_by_column(df, "unloading_qty")
            return df
        case _:
            raise NoDataFoundException(status.HTTP_204_NO_CONTENT, STATUS_TYPE_WARN,
                                       STATUS_DESC_NO_DATA + " document_name: " + str(document_name))


def flatten_json_by_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Flatten a JSON-like column into separate columns for each key in the dictionary,
    and drop the original column.

    :param df: Input DataFrame
    :param column_name: Column to be flattened
    :return: Modified DataFrame with new columns and the original column dropped
    """

    # Check if the column exists in the DataFrame
    if column_name not in df.columns:
        # raise ValueError(f"Column '{column_name}' not found in the DataFrame.")
        return df

    # Convert the stringified dictionaries to actual dictionaries
    df[column_name] = df[column_name].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    # Iterate over each row in the column and create new columns dynamically
    # Extract keys from the dictionaries and create separate columns for each key
    for idx, row in df[column_name].items():
        if isinstance(row, dict):
            for key, value in row.items():
                new_col_name = f"{column_name}_{key}"
                df.at[idx, new_col_name] = value

    # Drop the original column
    df = df.drop(columns=[column_name])
    return df