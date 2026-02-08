import threading

_thread_locals = threading.local()

def get_current_user():
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user
    return None

def get_current_request():
    return getattr(_thread_locals, 'request', None)

class AuditLogMiddleware:
    """
    Middleware to store the current request in thread-local storage.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        
        response = self.get_response(request)
        
        # Clean up
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
            
        return response
