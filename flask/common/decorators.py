from functools import wraps

from flask.common.auth import current_user


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user:
            return {'errors': {"auth": 'Not authenticated'}}, 401
        return func(*args, **kwargs)
    return wrapper
