# middleware.py

from django.utils.deprecation import MiddlewareMixin


class VisitTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # For non-logged-in users
        if not request.user.is_authenticated:
            visit_count = request.COOKIES.get('visit_count', '0')
            visit_count = int(visit_count) + 1
            response = self.get_response(request)
            response.set_cookie('visit_count', visit_count)
        else:
            # For logged-in users
            visit_count = request.session.get('visit_count', 0)
            visit_count += 1
            request.session['visit_count'] = visit_count
            response = self.get_response(request)

        return response
