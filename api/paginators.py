from rest_framework.pagination import PageNumberPagination

# Standard paginator for model views and view sets
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000