from functools import partial

from marshmallow import ValidationError
from mongoengine import ValidationError as MongoValidationError


def convert_to_instance(model, type_db, field='id', many=False, allow_deleted=False, check_deleted_by='state',
                        return_field=None, error='Could not find document.'):

    def get_value_from_instances(instances):
        """Get field in instances"""
        instances = instances if isinstance(instances, list) else [instances]
        return [getattr(doc, field) for doc in instances]

    def query(value, many_instances=False, **kwargs):
        """Query for sql/nosql database"""
        # Generate filter data
        query_field = f"{field}__in" if many_instances else field
        filter_data = {query_field: value}
        if allow_deleted:
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
        """
        Main func
        """
        value = str(args[0])
        try:
            result = convert_many(value, **kwargs) if many else convert_one(value, **kwargs)
        except MongoValidationError:
            raise ValidationError('Invalid identifier', field_name=field)
        if not result:
            raise ValidationError(error, field_name=field)
        return get_value_from_instances(result) if kwargs.get('return_field') else result

    return partial(to_instance, model=model, type_db=type_db, field=field,
                   many=many, error=error, return_field=return_field)
