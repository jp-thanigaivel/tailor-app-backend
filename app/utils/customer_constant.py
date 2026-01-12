from app.utils.app_constant import Q_FILTER_GREATER_EQ, Q_FILTER_OPR_GREATER_EQ, Q_FILTER_LESSER_EQ, Q_FILTER_EQUALS, \
    Q_FILTER_OPR_EQUALS, Q_FILTER_OPR_LESSER_EQ, Q_SORT_TYPE_ASC, Q_SORT_OPR_TYPE_ASC, Q_SORT_TYPE_DESC, \
    Q_SORT_OPR_TYPE_DESC

Q_ALLOWED_FILTER_FIELDS_customer = \
    {
        "customerId": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "customer_id",
            "field_type": "str"
        },
        "customerName": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "customer_name",
            "field_type": "str"
        },
        "createdOn": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "created_on",
            "field_type": "datetime"
        },
        "createdOn__gte": {
            "filter_type": Q_FILTER_GREATER_EQ,
            "filter_opr": Q_FILTER_OPR_GREATER_EQ,
            "field": "created_on",
            "field_type": "datetime"
        },
        "createdOn__lte": {
            "filter_type": Q_FILTER_LESSER_EQ,
            "filter_opr": Q_FILTER_OPR_LESSER_EQ,
            "field": "created_on",
            "field_type": "datetime"
        }
    }

Q_ALLOWED_SORT_FIELDS_customer = \
    {
        "updatedOn": {
            "sort_type": Q_SORT_TYPE_ASC,
            "sort_opr": Q_SORT_OPR_TYPE_ASC,
            "field": "updated_on",
            "field_type": "datetime"
        },
        "-updatedOn": {
            "sort_type": Q_SORT_TYPE_DESC,
            "sort_opr": Q_SORT_OPR_TYPE_DESC,
            "field": "updated_on",
            "field_type": "datetime"
        }
    }