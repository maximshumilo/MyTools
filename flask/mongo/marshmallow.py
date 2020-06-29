from functools import partial

from marshmallow import ValidationError
from mongoengine import ValidationError as MongoValidationError


def convert_to_instance(model, field='id', many=False, return_field=None, error='Could not find document.'):
    def get_value_from_instances(instances):
        """Get field in instances"""
        return [getattr(doc, field) for doc in instances]

    def convert_one(value, **kwargs):
        """Convert to one instance"""
        instance = model.objects.filter(**{field: value}).first()
        return get_value_from_instances([instance])[0] if kwargs.get('return_field') else instance

    def convert_many(value, **kwargs):
        """Convert to many instances"""
        values = value.split(',')
        values = list(set(values))
        items = model.objects.filter(**{f'{field}__in': values}).all()
        return get_value_from_instances(items) if kwargs.get('return_field') else items

    def to_instance(*args, **kwargs):
        """
        Main func

        """
        value = args[0]
        try:
            result = convert_many(value, **kwargs) if many else convert_one(value, **kwargs)
        except MongoValidationError:
            raise ValidationError('Invalid identifier', field_name=field)
        if not result:
            raise ValidationError(error, field_name=field)
        return result

    return partial(to_instance, model=model, field=field, many=many, error=error, return_field=return_field)
