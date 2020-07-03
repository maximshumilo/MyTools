import time


def check_run_time(count_decimal_places=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func(*args, **kwargs)
            finish_time = time.time()
            return finish_time-start_time
        return wrapper
    return decorator

