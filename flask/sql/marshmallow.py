from functools import partial

from marshmallow import ValidationError


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



