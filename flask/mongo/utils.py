from flask import request
from marshmallow import ValidationError
from mongoengine.errors import ValidationError as MongoValidationError


def load_params_get(schema, **kwargs):
    """ Check params from request (GET) """
    try:
        args, errors = schema(**kwargs).load(request.args)
    except ValidationError as exc:
        return None, {'errors': {exc.field_name: exc.message}}
    if errors:
        return None, errors
    return args, None


def check_params(schema, exclude_list=None, only_fields=None, partial=False):
    """ Check params from request (POST, PUT, DELETE). JSON format """
    if exclude_list is None:
        exclude_list = []
    if not request.is_json:
        return {"errors": {"common": "Cannot parse json"}}, 400
    return schema(exclude=exclude_list, only=only_fields, partial=partial).load(request.json)


def save_doc(obj):
    """ Save doc in mongodb """
    try:
        obj.save()
    except MongoValidationError as exc:
        errors = {field: str(error) for field, error in exc.errors.items()}
        return {"errors": errors}, 400
    return {}, 200
