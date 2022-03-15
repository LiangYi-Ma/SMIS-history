from django.utils.deprecation import MiddlewareMixin


class theMiddleWare(MiddlewareMixin):
    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = "127.0.0.1:9527"
        return response
