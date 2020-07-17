import time
from typing import Any


def check_run_time(count_decimal_places: int = 2) -> Any:
    """
    Проверка времени выполнения функции

    :param count_decimal_places Количество знаков после запятой
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            func(*args, **kwargs)
            finish_time = time.time()
            return finish_time-start_time
        return wrapper
    return decorator

