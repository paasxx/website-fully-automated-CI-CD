from rest_framework.pagination import CursorPagination


class TransactionCursorPagination(CursorPagination):
    page_size = 50
    # date alone is not unique — adding id guarantees deterministic ordering
    # so the cursor never skips or duplicates rows across pages.
    ordering = ("-date", "id")
    cursor_query_param = "cursor"
    page_size_query_param = "page_size"
    max_page_size = 200
