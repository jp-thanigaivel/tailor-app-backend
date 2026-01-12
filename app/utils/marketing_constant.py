from app.utils.app_constant import Q_FILTER_GREATER_EQ, Q_FILTER_OPR_GREATER_EQ, Q_FILTER_LESSER_EQ, Q_FILTER_EQUALS, \
    Q_FILTER_OPR_EQUALS, Q_FILTER_OPR_LESSER_EQ, Q_SORT_TYPE_ASC, Q_SORT_OPR_TYPE_ASC, Q_SORT_TYPE_DESC, \
    Q_SORT_OPR_TYPE_DESC

Q_ALLOWED_FILTER_FIELDS_marketing = \
    {
        "marketingId": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "marketing_id",
            "field_type": "str"
        },
        "customerId": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "customer_id",
            "field_type": "str"
        },
        "enquiryDate": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "enquiry_date",
            "field_type": "datetime"
        },
        "enquiryDate_gte": {
            "filter_type": Q_FILTER_GREATER_EQ,
            "filter_opr": Q_FILTER_OPR_GREATER_EQ,
            "field": "enquiry_date",
            "field_type": "datetime"
        },
        "enquiryDate__lte": {
            "filter_type": Q_FILTER_LESSER_EQ,
            "filter_opr": Q_FILTER_OPR_LESSER_EQ,
            "field": "enquiry_date",
            "field_type": "datetime"
        },
        "siteLocation": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "site_location",
            "field_type": "str"
        },
        "commitedDate": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "commited_date",
            "field_type": "datetime"
        },
        "commitedDate_gte": {
            "filter_type": Q_FILTER_GREATER_EQ,
            "filter_opr": Q_FILTER_OPR_GREATER_EQ,
            "field": "commited_date",
            "field_type": "datetime"
        },
        "commitedDate__lte": {
            "filter_type": Q_FILTER_LESSER_EQ,
            "filter_opr": Q_FILTER_OPR_LESSER_EQ,
            "field": "commited_date",
            "field_type": "datetime"
        },
        "orderStatus": {
            "filter_type": Q_FILTER_EQUALS,
            "filter_opr": Q_FILTER_OPR_EQUALS,
            "field": "order_status",
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

Q_ALLOWED_SORT_FIELDS_marketing = \
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