"""Custom DRF exception handler that avoids leaking sensitive information."""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Call DRF's default exception handler first, then customize the format.
    Avoids leaking stack traces or implementation details in error responses.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Flatten DRF's nested detail structure into a uniform format
        error_data = {
            "status": "error",
            "code": response.status_code,
            "errors": response.data,
        }
        response.data = error_data

    return response
