from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Класс пагинации для API запросов"""
    page_size_query_param = 'limit'
