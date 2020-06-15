from functools import wraps

from marshmallow import ValidationError

from flask import request


def convert_to_instance(model):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            doc = model.where(**{'id': kwargs.get('category'), "state__ne": "deleted"}).first()
            if not doc:
                return {'errors': {"url": 'Не найден документ с таким идентификатором'}}, 400
            kwargs['category'] = doc
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_params(schema, **schema_params):
    """
    Функция для получения параметров запроса

    :param schema: Схема валидации и загрузки параметров.
    :param schema_params: exclude=[], only=[], partial=True/False, unknown='exclude'
    :return: Параметры запроса
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = None
            if request.method == 'GET':
                data = request.args
            elif request.method in ['POST', 'PUT', 'DELETE']:
                if not request.is_json:
                    return {'errors': {"common": "Cannot parse json"}}, 400
                data = request.json

            # Load params
            try:
                params = (schema(**schema_params).load(data),)
            except ValidationError as exc:
                return {'errors': exc.messages}, 400
            args += params
            return func(*args, **kwargs)
        return wrapper
    return decorator
