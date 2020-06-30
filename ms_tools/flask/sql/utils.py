from functools import reduce

from natsort import natsorted, ns
from sqlalchemy import desc


def query_filter(query=None, **params):
    """
    Фильтрация Query

    Если параметр фильтрации начинается на 'q_', то фильтруется по вхождению без учета регистра
    Если параметр фильтрации заканчивается на '_in', то фильтреутся по вхождению в данный список. ( _in - все что входит в этот список)
    Если параметр фильтрации заканчивается на '_nin', то фильтреутся по иселючению из данного списка. ( _nin - все кроме этого списка)
    Если параметр фильтрации заканчивается на '_gte' - больше либо равно
    Если параметр фильтрации заканчивается на '_lte' - меньше либо равно
    Если параметр фильтрации заканчивается на '_ne' - возвращабтся все документы где это не равно этому значению"
    В остальных случаях фильтруется по полному совпадению
    """
    if params.get('limit', None) is not None:
        params.pop('limit')
    if params.get('offset', None) is not None:
        params.pop('offset')
    if params.get('order_by', None) is not None:
        params.pop('order_by')

    many_filter_fields = []
    params_filter = {}
    # params = {key: value for key, value in params.items() if value is not None}
    for key, value in params.items():
        dict_key = key.split(',')
        for arg in dict_key:
            newkey = key
            if arg.startswith('q_') and value is not None:
                newkey = arg[2:] + '__ilike'
                value = f"%{value}%"
            elif arg.endswith('_in') and isinstance(value, list):
                newkey = arg[:-3] + '__in'
            elif arg.endswith('_nin') and isinstance(value, list):
                newkey = arg[:-4] + '__nin'
            elif arg.endswith('_gte'):
                newkey = arg[:-4] + '__ge'
            elif arg.endswith('_lte'):
                newkey = arg[:-4] + '__le'
            elif arg.endswith('_ne'):
                newkey = arg[:-3] + '__ne'
            if len(dict_key) > 1:
                continue
            else:
                params_filter.update({newkey: value})
    many_filter_fields = reduce(lambda a, b: a | b, many_filter_fields) if many_filter_fields else None

    # Filter value for many fields & Default filter
    query = query(many_filter_fields) if many_filter_fields else query
    query = query.where(**params_filter)

    return query


def natural_sorted(ordering_list, field=None, ignore_case=None, **kwargs):
    """
        Сортировка приближеная к реальной. Используется библиотека natsort.

        a = ['version10', 'version11', 'version111', 'version12']

        # Default sorting
        RUN: sorted(a)
        ['version10', 'version11', 'version111', 'version12']

        # Natural sorting
        RUN: natural_sorted(a)
        ['version10', 'version11', 'version12', 'version111']

    :param ordering_list: Список, который необходимы отсортировать.
    :param field: Поле, по которому нужно отсортировать. (Если это список объектов)
    :param ignore_case: Флаг, игнорировать регистр.
    :param kwargs:
    :return:
    """

    if field.startswith('-'):
        field = field[1:]
        kwargs['reverse'] = True
    if isinstance(ordering_list[0], object):
        kwargs['key'] = lambda x: '' if field not in x.columns else getattr(x, field)
    if ignore_case:
        kwargs['alg'] = ns.IGNORECASE
    return natsorted(ordering_list, **kwargs)


def offset_limit_order(qs, natural_sort=True, **kwargs):
    """
    Функция для сортировки, смещения и установки лимита для QuerySet

    :param qs: QuerySet
    :param natural_sort: Флаг метода натуральной сортировки. (По умолчанию - True)
    :return: Обработаный QuerySet возвращается в виде спсика (list)
    """
    if qs.count() == 0:
        return list(qs)
    if kwargs.get('order_by'):
        if natural_sort:
            qs = natural_sorted(qs, field=kwargs['order_by'])
        else:
            if kwargs['order_by'].startswith('-'):
                qs = qs.order_by(desc(kwargs['order_by'][1:]))
            else:
                qs = qs.order_by(kwargs['order_by'])
    qs = qs.all() if not isinstance(qs, list) else qs
    if kwargs.get('offset'):
        qs = qs[kwargs['offset']:]
    if kwargs.get('limit'):
        qs = qs[:kwargs['limit']]
    return qs
