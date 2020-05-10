from functools import partial

from marshmallow import ValidationError


def convert_to_instance(model, field='id', many=False, return_field=None, error='', field_type=int):
    def to_instance(value, context, model, field, many, error, return_field, field_type):
        if error:
            _error = error
        # Если указано несколько идентификаторов
        if many:
            # Удаляем дубликаты
            value = list(set(value.split(','))) if not isinstance(value, list) else list(set(value))

            # Получаем документы из базы
            docs = [model.where(**{field: int(_id)}).first() for _id in value]
            if not docs:
                if not error:
                    _error = 'По данным идентификаторам, ничего не найдено'
                raise ValidationError(_error, field_name=field)
            if len(value) != len(docs):
                if not error:
                    _error = 'Неверно указан один или несколько идентификаторов'
                raise ValidationError(_error, field_name=field)
            if return_field and return_field in model.columns:
                docs = [item.to_dict()[return_field] for item in docs]
            return docs

        # Если указан один идентификатор
        if not error:
            _error = 'Неверный формат идентификатора'
        if field_type == int and type(value) in [bool, float]:
            raise ValidationError(_error, field_name=field)
        else:
            try:
                value = field_type(value)
            except Exception:
                raise ValidationError(_error, field_name=field)
            doc = model.where(**{field: value, "state__ne": "deleted"}).first()
            if not doc:
                if not error:
                    _error = 'Не найден документ с таким идентификатором'
                raise ValidationError(_error, field_names=field)
            return doc.to_dict()[return_field] if return_field else doc

    if return_field is True:
        return_field = field

    return partial(to_instance, model=model, field=field, many=many, error=error, return_field=return_field,
                   field_type=field_type)


def to_list_range_int(field_name='price_range'):
    def to_instance(price_range_str, context, field_name):
        range_values = [0, 0]
        if not price_range_str:
            return range_values
        range_values = price_range_str.split(',')
        for k, value in enumerate(range_values):
            if value:
                try:
                    range_values[k] = int(value)
                except Exception:
                    error = 'Одно из поданых значений не является числом'
                    raise ValidationError(error, field_name=field_name)
            else:
                range_values[k] = 0
        return range_values

    return partial(to_instance, field_name=field_name)


def if_null(field_name, null_value=None, empties=None):
    def inner(obj, context, field_name, null_value, empties):
        value = getattr(obj, field_name)
        if value in empties:
            return null_value
        return value

    if empties is None:
        empties = [None]

    return partial(inner, field_name=field_name, null_value=null_value, empties=empties)


def to_list(validate_items=str, field_name='price_range'):
    def to_instance(value, context, validate, field=field_name):
        if not value:
            return []
        list_values = list(set(value.split(',')))
        for k, item in enumerate(list_values):
            try:
                if validate == bool:
                    list_values[k] = item == 'true'
                else:
                    list_values[k] = validate(item)
            except Exception:
                error = f'Один из параметров имеет неверный тип данных. Ожидается: {validate.__name__} '
                raise ValidationError(error, field_name=field)
        return list_values

    return partial(to_instance, validate=validate_items, field=field_name)
