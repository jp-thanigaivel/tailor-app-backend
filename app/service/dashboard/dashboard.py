import logging
from typing import Any

import pandas as pd

from app.constants.marketing import MarketingModelKeyEnum, MarketingKeyEnum, MarketingOrderStatus
from app.common.models import TokenData
from app.service.marketing.marketing import marketing_by_range
from app.utils.app_constant import RES_C_KEY_DATA

logger = logging.getLogger(__name__)

unit_conversion = {
        "KG": 1,
        "TON": 1000,
        "LBS": 0.453592,
    }


def get_marketing_by_period(query_param: dict[str, str], token_data: TokenData) -> dict[str, Any]:
    logger.info("get_marketing_by_period query_param: %s", query_param)
    df = _get_df_by_query_param(query_param, token_data)
    df = _get_slice_range(query_param, df)
    logger.info("Grouping data by period and order status")
    status_summary = df.groupby(['period', MarketingModelKeyEnum.ORDER_STATUS.value]).size().unstack(fill_value=0)

    return status_summary.to_dict()


def get_monthly_revenue(query_param: dict[str, str], token_data: TokenData) -> dict[str, Any]:
    query_param[MarketingKeyEnum.ORDER_STATUS.value] = MarketingOrderStatus.CONFIRMED.value
    df = _get_df_by_query_param(query_param, token_data)
    # Convert to datetime and extract month
    df[MarketingModelKeyEnum.ENQUIRY_DATE.value] = pd.to_datetime(df[MarketingModelKeyEnum.ENQUIRY_DATE.value])
    df['month'] = df[MarketingModelKeyEnum.ENQUIRY_DATE.value].dt.to_period('M').astype(str)

    # Calculate the revenue for each order (quantity * unit price)
    logger.info("Calculating revenue for each order")
    #df['revenue'] = df['qty'].apply(lambda x: x['qty'] * df['unit_price'].apply(lambda y: y['price']))
    df['revenue'] = df.apply(lambda row: row['qty']['qty'] * row['unit_price']['price'], axis=1)

    # Group by month and calculate total revenue
    logger.info("Grouping data by month and calculating total revenue")
    monthly_revenue = df.groupby('month')['revenue'].sum()

    return monthly_revenue.to_dict()


def get_grouped_products(query_param: dict[str, str], token_data: TokenData)-> dict[str, Any]:
    query_param[MarketingKeyEnum.ORDER_STATUS.value] = MarketingOrderStatus.CONFIRMED.value
    df = _get_df_by_query_param(query_param, token_data)
    df = _get_slice_range(query_param, df)

    """
    # Extract the quantity
    #df['qty'] = df['qty'].apply(lambda x: x['qty'])  # Get the quantity value
    # grouped_products = df.groupby('concrete_grade')['qty'].sum()

    df['qty_value'] = df['qty'].apply(lambda x: x['qty'])
    grouped_products = df.groupby(['concrete_grade', df['qty'].apply(lambda x: x['unit'])]) \
        .agg(total_qty=('qty_value', 'sum')) \
        .reset_index()
    grouped_products.columns = ['concrete_grade', 'unit', 'total_qty']
    """

    # Extract quantity value from 'qty' dictionary
    df['qty_value'] = df['qty'].apply(lambda x: x['qty'])
    df['unit'] = df['qty'].apply(lambda x: x['unit'])
    grouped_products = df.groupby(['concrete_grade', 'unit', 'period'])['qty_value'].sum().reset_index()

    return grouped_products.to_dict(orient='records')

def _get_df_by_query_param(query_param: dict[str, str], token_data: TokenData) -> pd.DataFrame:
    logger.info("Fetching marketing data with query_param: %s", query_param)
    db_response_data: dict[str, Any] = marketing_by_range(query_param, token_data)

    logger.info("Converting db_response to DF")
    df = pd.DataFrame(db_response_data[RES_C_KEY_DATA])
    logger.info("DataFrame created with shape: %s", df.shape)
    return df

def _get_slice_range(query_param: dict[str, str], df: pd.DataFrame) -> pd.DataFrame:
    period: str = query_param.get("period", "day")
    if period == "day":
        df['period'] = df[MarketingModelKeyEnum.ENQUIRY_DATE.value].dt.date.astype(str)
    elif period == "month":
        df['period'] = df[MarketingModelKeyEnum.ENQUIRY_DATE.value].dt.to_period('M').astype(str)
    elif period == "year":
        df['period'] = df[MarketingModelKeyEnum.ENQUIRY_DATE.value].dt.year.astype(str)
    return df