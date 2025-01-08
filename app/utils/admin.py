from functools import wraps
from flask import g
from flask_jwt_extended import verify_jwt_in_request
from ..utils.error_codes import *

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if not g.user.is_admin:
            return {
                'status': 'error',
                'code': PERMISSION_DENIED,
                'message': get_error_message(PERMISSION_DENIED)
            }, 403
        return fn(*args, **kwargs)
    return wrapper 