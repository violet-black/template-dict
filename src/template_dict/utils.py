from typing import Any, List, Union

__all__ = ['get_field']


def get_field(__obj, __key: Union[str, List[str]], *, default: Union[Exception, Any] = KeyError, delimiter: str = '.'):
    """Get a field from a nested dict using a flattened key.

    >>> get_field({'a': {'b': [1], 'c': 2}}, 'a.b')
    [1]

    using a custom delimiter:

    >>> get_field({'a': [{'b': 1}, {'b': 2}, {}]}, 'a-b', default=None, delimiter='-')
    [1, 2, None]

    aggregate from a list:

    >>> get_field([{'b': {'c': [{'d': 1}, {'d': 2}, {}]}}, {'b': 3}], 'b.c.d', default=None)
    [[1, 2, None], None]

    raise an error on default if default is an exception

    >>> get_field({}, 'a.b.c')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    KeyError: ['a', 'b', 'c']

    """
    # if type(obj) is dict and key in obj:
    #     return obj[key]

    if isinstance(__key, str):
        __key = __key.split(delimiter)

    for n, _key in enumerate(__key):
        if _key:
            if isinstance(__obj, dict):
                if _key in __obj:
                    __obj = __obj[_key]
                else:
                    if type(default) is type:
                        if issubclass(default, Exception):
                            raise default(__key)
                    return default
            elif isinstance(__obj, (list, tuple)):
                __obj = type(__obj)(
                    get_field(sub_obj, __key[n:], default=default, delimiter=delimiter) for sub_obj in __obj
                )
                return __obj
            else:
                return default

    return __obj
