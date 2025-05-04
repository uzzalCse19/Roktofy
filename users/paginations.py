from rest_framework.pagination import PageNumberPagination

class UserPagination(PageNumberPagination):
    page_size = 20  
    page_size_query_param = 'page_size'  
    max_page_size = 100  
    def get_page_size(self, request):
        """"
        get_page_size 
        """
        page_size = super().get_page_size(request)
        if page_size is None:
            return self.page_size  
        return min(page_size, self.max_page_size)  