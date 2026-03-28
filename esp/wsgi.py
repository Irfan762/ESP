"""
esp/wsgi.py
-----------
Custom WSGI application that fixes a Python 3.12 + Django live_server
compatibility issue where wsgiref passes PATH_INFO as bytes instead of str,
causing `TypeError: startswith first arg must be str or a tuple of str, not bytes`
in Django's LiveServerTestCase._should_handle().

This wraps the standard Django WSGI app and decodes any bytes environ values
before they reach Django's routing layer.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "esp.settings")


class BytesFixMiddleware:
    """
    WSGI middleware that ensures PATH_INFO and SCRIPT_NAME are always str.
    Needed for Python 3.12 + wsgiref + Django live_server.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        for key in ("PATH_INFO", "SCRIPT_NAME", "REQUEST_URI", "QUERY_STRING"):
            if key in environ and isinstance(environ[key], bytes):
                environ[key] = environ[key].decode("utf-8", errors="replace")
        return self.app(environ, start_response)


application = BytesFixMiddleware(get_wsgi_application())
