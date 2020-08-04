from functools import wraps

from marshmallow import ValidationError

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


def convert_to_instance(
        model,
        type_db: str,
        field: str = 'id',
        allow_deleted: bool = False,
        check_deleted_by: str = 'state',
        optional_filter: dict = None,
        error: str = 'Could not find document.'):
    """
    Convert to instance decorator

    :param model: Model
    :param type_db: Type database (sql/nosql)
    :param field: Convert to instance by field in model. Equal in url var name in urls.py. /api/examples/<var_name>/
    :param allow_deleted: Allow return deleted instance
    :param check_deleted_by: Check deleted by field
    :param optional_filter Optional filter
    :param error Error message, by not found document
    :return Instance or error
    """
    if optional_filter is None:
        optional_filter = {}

    def to_instance_nosql(filter_data):
        """Convert to instance from nosql db"""
        from mongoengine import ValidationError as MongoValidationError
        try:
            return model.objects.filter(**filter_data).first(), None
        except MongoValidationError:
            return None, {'errors': {field: 'Invalid data'}}

    def to_instance_sql(filter_data):
        """Convert to instance from sql db"""
        return model.where(**filter_data).first(), None

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Main func"""
            filter_data = {field: kwargs.pop(field), **optional_filter}
            if not allow_deleted:
                filter_data.update({f'{check_deleted_by}__ne': 'deleted'})
            doc, errors = to_instance_nosql(filter_data) if type_db == 'nosql' else to_instance_sql(filter_data)
            if errors:
                return errors, 400
            if not doc:
                return {'errors': {field: error}}, 400
            args += (doc,)
            return func(*args, **kwargs)
        return wrapper
    return decorator
