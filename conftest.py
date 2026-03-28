"""
Root conftest.py
----------------
Compatibility patch for Django 6.0 + Python 3.12 + wsgiref.

ISSUE: wsgiref on Python 3.12 passes PATH_INFO as bytes (PEP 3333 violation).
Django's FSFilesHandler._should_handle() receives the result of
get_path_info(environ). get_path_info calls get_bytes_from_wsgi which calls
value.encode('iso-8859-1') — but bytes has no .encode(), so it crashes.

The crash happens inside the live_server thread, causing every HTTP request
to return a 500 before Django's URL router is even reached.

FIX: Patch FSFilesHandler._should_handle to decode bytes path to str.
This is the most targeted fix — it doesn't touch get_path_info internals
and works regardless of how testcases.py imported its dependencies.
"""

import django.test.testcases as _tc


_orig_should_handle = _tc.FSFilesHandler._should_handle


def _safe_should_handle(self, path):
    """
    Decode bytes path to str before calling startswith.
    Needed when wsgiref passes PATH_INFO as bytes on Python 3.12.
    """
    if isinstance(path, (bytes, Exception)):
        # get_path_info crashed and returned an exception object, or bytes
        # Fall back to not handling (let the main WSGI app handle it)
        try:
            path = path.decode("utf-8", errors="replace")
        except AttributeError:
            return False
    return _orig_should_handle(self, path)


_tc.FSFilesHandler._should_handle = _safe_should_handle


# Also patch __call__ to prevent get_path_info from crashing entirely
# by ensuring PATH_INFO is always str before it's read
_orig_fs_call = _tc.FSFilesHandler.__call__


def _safe_fs_call(self, environ, start_response):
    """Ensure PATH_INFO is str before Django's handler reads it."""
    if isinstance(environ.get("PATH_INFO"), bytes):
        environ = dict(environ)
        environ["PATH_INFO"] = environ["PATH_INFO"].decode("utf-8", errors="replace")
    try:
        return _orig_fs_call(self, environ, start_response)
    except TypeError:
        # If get_path_info still fails, skip static handling and pass through
        return self.application(environ, start_response)


_tc.FSFilesHandler.__call__ = _safe_fs_call
