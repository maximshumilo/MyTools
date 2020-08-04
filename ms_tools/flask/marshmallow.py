from functools import partial
from typing import Any

from marshmallow import ValidationError
from mongoengine import ValidationError as MongoValidationError


def convert_to_instance(
        model: Any,
        type_db: str,
        field: str = 'id',
        many: bool = False,
        allow_deleted: bool = True,
        check_deleted_by: str = 'state',
        return_field: str = None,
        error: str = 'Could not find document.'):
    """
    Convert to instance

    :param model The model to which you want to convert
    :param type_db Database type (sql/nosql)
    :param field The field that will be converted
    :param many Convert to many instances flag
    :param allow_deleted Allowed return deleted instances flag
    :param check_deleted_by Filed, by check deleted instances. (If allow_deleted=False)
    :param return_field Return value field in current instance
    :param error Error message, by not found document
    :return Instance or value field in instance or errors

        Example:
            data = {"attribute_name": 123456}
            ...
            class ClassName(Schema):
                attribute_name = fields.Function(deserialize=to_instance(User, 'nosql'))
            ...
            result = ClassName().load(data)     # {"attribute_name": UserInstance}
    """

    def get_value_from_instances(instances, **kwargs):
        """Get field in instances"""
        instances = instances if isinstance(instances, list) else [instances]
        fields = model.columns if kwargs['type_db'] == 'sql' else model._fields.keys()
        if return_field in fields:
            return [getattr(doc, return_field) for doc in instances]
        raise ValidationError("Field not found in model")

    def query(value, many_instances=False, **kwargs):
        """Query for sql/nosql database"""
        # Generate filter data
        query_field = f"{field}__in" if many_instances else field
        filter_data = {query_field: value}
        if not allow_deleted:
            filter_data.update({f'{check_deleted_by}__ne': 'deleted'})

        # Generate query
        if kwargs['type_db'] == 'sql':
            return model.where(**filter_data)
        elif kwargs['type_db'] == 'nosql':
            return model.objects.filter(**{query_field: value})
        else:
            ValidationError(error, field_name=field)

    def convert_one(value, **kwargs):
        """Convert to one instance"""
        return query(value, **kwargs).first()

    def convert_many(value, **kwargs):
        """Convert to many instances"""
        values = value.split(',')
        values = list(set(values))
        return query(values, many_instances=True, **kwargs).all()

    def to_instance(*args, **kwargs):
        """Main func"""
        value = str(args[0])
        try:
            result = convert_many(value, **kwargs) if many else convert_one(value, **kwargs)
        except MongoValidationError:
            raise ValidationError('Invalid identifier', field_name=field)
        if not result:
            raise ValidationError(error, field_name=field)
        return get_value_from_instances(result, **kwargs) if kwargs.get('return_field') else result

    return partial(to_instance, model=model, type_db=type_db, field=field,
                   many=many, error=error, return_field=return_field)

