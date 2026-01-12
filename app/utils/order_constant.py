from app.utils.app_constant import Q_FILTER_GREATER_EQ, Q_FILTER_OPR_GREATER_EQ, Q_FILTER_LESSER_EQ, Q_FILTER_EQUALS, \
    Q_FILTER_OPR_EQUALS, Q_FILTER_OPR_LESSER_EQ, Q_SORT_TYPE_ASC, Q_SORT_OPR_TYPE_ASC, Q_SORT_TYPE_DESC, \
    Q_SORT_OPR_TYPE_DESC

Q_ALLOWED_FILTER_FIELDS_order = \
    {
        "orderId": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "orderId",
            "field_type": "str"
        },
        "customerId": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "customerId",
            "field_type": "str"
        },
        "orderStatus": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "orderStatus",
            "field_type": "str"
        },
        "status": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "orderStatus",
            "field_type": "str"
        },
        "createdOn": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "createdOn",
            "field_type": "datetime"
        },
        "createdOn__gte": {
            "filter_type": Q_FILTER_GREATER_EQ,
            "filter_opr": Q_FILTER_OPR_GREATER_EQ,
            "field": "createdOn",
            "field_type": "datetime"
        },
        "createdOn__lte": {
            "filter_type": Q_FILTER_LESSER_EQ,
            "filter_opr": Q_FILTER_OPR_LESSER_EQ,
            "field": "createdOn",
            "field_type": "datetime"
        }
    }

Q_ALLOWED_SORT_FIELDS_order = \
    {
        "updatedOn": {
            "sort_type": Q_SORT_TYPE_ASC,
            "sort_opr": Q_SORT_OPR_TYPE_ASC,
            "field": "updatedOn",
            "field_type": "datetime"
        },
        "-updatedOn": {
            "sort_type": Q_SORT_TYPE_DESC,
            "sort_opr": Q_SORT_OPR_TYPE_DESC,
            "field": "updatedOn",
            "field_type": "datetime"
        },
        "_id": {
            "sort_type": Q_SORT_TYPE_ASC,
            "sort_opr": Q_SORT_OPR_TYPE_ASC,
            "field": "_id",
            "field_type": "str"
        },
        "-_id": {
            "sort_type": Q_SORT_TYPE_DESC,
            "sort_opr": Q_SORT_OPR_TYPE_DESC,
            "field": "_id",
            "field_type": "str"
        }
    }
