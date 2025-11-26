from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import status
from django.conf import settings

import time
import uuid

#============================================================== exception handler util ===============================================================================
def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        # An exception occurred during request processing
        error_code = 500  # Internal Server Error
        error_message = str(exc)  # Get the exception message
        print(f"Error {error_code}: {error_message}")
        
        # Return a JSON response with error details
        return Response(
            data={'error': error_message},
            status=error_code,
            content_type='application/json'
        )

    elif response.status_code >= 400:
        # Client or server error response
        response.data['status_code'] = response.status_code
        response.data['error'] = response.data.get('detail', 'Error')

        # Return the modified response as JSON
        return Response(
            data=response.data,
            status=response.status_code,
            content_type='application/json'
        )

    return response



    