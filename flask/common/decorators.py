from functools import wraps

from marshmallow import ValidationError
from mongoengine import ValidationError as MongoValidationError

from flask import request


def get_params(schema, **schema_params):
    """
    Getting request parameters

    :param schema: Marshmallow schema
    :param schema_params: exclude=[], only=[], partial=True/False, unknown='exclude'
    :return: request params
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


def convert_to_instance(type_db, model, convert_by_field='id', allow_deleted=False, check_deleted_by='state'):
    """
    Convert to instance decorator

    :param type_db: Type database (sql/nosql)
    :param model: Model
    :param convert_by_field: Convert to instance by field in model
    :param allow_deleted: Allow return deleted instance
    :param check_deleted_by: Check deleted by field
    :return: Instance or error
    """
    def to_instance_nosql(filter_data):
        try:
            return model.objects.filter(**filter_data).first(), None
        except MongoValidationError:
            return None, {'errors': {convert_by_field: 'Invalid id'}}

    def to_instance_sql(filter_data):
        return model.where(**filter_data).first()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            filter_data = {convert_by_field: kwargs.pop(convert_by_field)}
            if not allow_deleted:
                filter_data.update({f'{check_deleted_by}__ne': 'deleted'})
            doc, errors = to_instance_nosql(filter_data) if type_db == 'no_sql' else to_instance_sql(filter_data)
            if errors:
                return errors, 400
            if not doc:
                return {'errors': {convert_by_field: 'Document not found'}}, 400
            args += (doc,)
            return func(*args, **kwargs)
        return wrapper
    return decorator
