from abc import ABC, abstractmethod
from ast import literal_eval
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Type, Union
from uuid import uuid4

from template_dict.utils import get_field

__all__ = ["Definitions", "Template", "FUNCTIONS", "OPERATORS"]


@dataclass
class Definitions:
    """Template definitions."""

    operator_brackets: str = "[]"
    operator_sign: str = "!"
    operator_delimiter: str = ":"
    key_delimiter: str = "."
    empty_default: Union[Exception, Any] = KeyError
    fmt_empty_default: Union[Exception, str] = "-"
    fmt_key_delimiter: str = "-"
    fmt_join_delimiter: str = ","
    default_operator: str = "s"
    escape_quote: str = "`"


class Operator(ABC):
    """Base operator object."""

    __slots__ = ("template", "args")

    def __init__(self, template: "Template", args: tuple) -> None:
        """Initialize operator object."""
        self.template = template
        self.args = args if args else tuple()

    def __call__(self, data: Mapping[str, Any], /):
        """Call an operator with dynamic data."""
        args = tuple(self._eval_args(data))
        return self.eval(args, data)

    @abstractmethod
    def eval(self, args: tuple, data: Mapping, /):
        """Evaluate arguments using provided data.

        This method should contain operator-specific evaluation logic.

        :param args: a tuple of already evaluated arguments
        :param data: dynamic data
        :returns: evaluated operator value
        """
        ...

    def _eval_args(self, data: Mapping[str, Any], /):
        for arg in self.args:
            if isinstance(arg, Operator):
                arg = arg(data)
            yield arg


class OperatorSelect(Operator):
    """Select value operator.

    >>> Template('[x]').eval({'x': 42})
    42

    Select with default evaluated value:

    >>> Template('[x:42]').eval({})
    42

    """

    def eval(self, args: tuple, data: Mapping[str, Any], /):
        arg, default = args[0], self.template.definitions.empty_default
        if len(args) > 1:
            default = args[1]
            if not isinstance(default, Operator):
                with suppress(Exception):
                    default = literal_eval(args[1])
        result = get_field(data, arg, delimiter=self.template.definitions.key_delimiter, default=default)
        return result


class OperatorExec(Operator):
    """Execute a function defined in :py:obj:`template_dict.templates.FUNCTIONS`.

    >>> Template('[!x:max:[x]:[y]]').eval({'x': 1, 'y': 2})
    2

    """

    def eval(self, args: tuple, data: Mapping[str, Any], /):
        func_name, args = args[0], args[1:]
        func_args = []
        for arg, value in zip(self.args[1:], args):
            if isinstance(arg, str):
                value = literal_eval(value)
            func_args.append(value)
        f = self.template.functions[func_name]
        return f(func_args)


class OperatorFormat(Operator):
    """String format operator.

    >>> Template('[!f:{user-name} {user-last_name}]').eval({'user': {'name': 'John', 'last_name': 'Dowe'}})
    'John Dowe'

    Join multiple formatted strings:

    >>> Template('[!f:Sir {name}:Sir {last_name}]').eval({'name': 'John', 'last_name': 'Dowe'})
    'Sir John,Sir Dowe'

    """

    class _FormatDict(Mapping):

        __slots__ = ("data", "default", "delimiter")

        def __init__(self, data: Mapping[str, Any], default: Union[Any, Exception], delimiter: str):
            self.data = data
            self.default = default
            self.delimiter = delimiter

        def __getitem__(self, item: str, /):
            return get_field(self.data, item, default=self.default, delimiter=self.delimiter)

        def __len__(self):
            return len(self.data)

        def __iter__(self):
            return iter(self.data)

    def eval(self, args: tuple, data: Mapping[str, Any], /):
        data = self._FormatDict(
            data, self.template.definitions.fmt_empty_default, self.template.definitions.fmt_key_delimiter
        )
        result = self.template.definitions.fmt_join_delimiter.join(arg.format_map(data) for arg in args)
        return result


OPERATORS: Dict[str, Type[Operator]] = {
    "s": OperatorSelect,
    "x": OperatorExec,
    "f": OperatorFormat,
}

FUNCTIONS: Dict[str, Callable] = {
    # type conversion
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    # math
    "min": min,
    "max": max,
    "sum": sum,
    # generators
    "timestamp": lambda: datetime.now().astimezone(),
    "uuid": uuid4,
}


class Template:
    """Template dictionary.

    You can use it to fill a dictionary schema with data dynamically.

    Examples
    ________

    Return a plain value:

    >>> Template('value').eval({})
    'value'

    >>> Template(42).eval({})
    42

    Select nested keys with dot:

    >>> Template('[inner.key]').eval(({'inner': {'key': 'dogs'}}))
    'dogs'

    Select or default value:

    >>> Template("[key:'default']").eval({})
    'default'

    Nested operator:

    >>> Template('[key:[default]]').eval({'default': 'dogs'})
    'dogs'

    Eval Python object through select:

    >>> Template('[_:True]').eval({})
    True

    Format string with data:

    >>> Template('[!f:{user-name} {user-last_name}]').eval({'user': {'name': 'John', 'last_name': 'Dowe'}})
    'John Dowe'

    Call a function with parameters:

    >>> Template('[!x:max:[x]:[y]]').eval({'x': 1, 'y': 2})
    2

    Escape a string:

    >>> Template('`[name]`').eval({'name': 'escaped'})
    '[name]'

    Evaluate an array:

    >>> Template(['[name]', '[name]', '[name]']).eval({'name': 'dogs'})
    ['dogs', 'dogs', 'dogs']

    Evaluate a nested object:

    >>> Template({'nested': {'value': '[name]'}}).eval({'name': 'dogs'})
    {'nested': {'value': 'dogs'}}

    Unbalanced brackets would cause a ValueError

    >>> Template('[name').eval({'name': 'dogs'})  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ValueError: Unbalanced brackets in template: key="None", value="[name".

    """

    __slots__ = ("schema", "definitions", "operators", "functions", "condition_functions", "_schema", "keys")

    def __init__(
        self,
        schema: Any,
        *,
        definitions: Optional[Definitions] = None,
        operators: Optional[Mapping[str, Type[Operator]]] = None,
        functions: Optional[Mapping[str, Callable]] = None,
    ):
        """Initialize.

        :param schema: Template schema.
        :param definitions: set of definitions for the schema parser
        :param operators: set of operators defined for this schema
        :param functions: set of functions defined for this schema `exec` operator
        """
        self.schema = schema
        self.definitions = definitions or Definitions()
        self.operators = operators or OPERATORS
        self.functions = functions or FUNCTIONS
        keys: List[str] = []
        self._schema = self._parse_value(self.schema, keys)
        self.keys = frozenset(keys)

    def json_repr(self) -> dict:
        return {"schema": self.schema}

    def eval(self, data: Mapping[str, Any], /):
        """Fill the template schema with dynamic data."""
        return self._fill_value(self._schema, data)

    def _fill_value(self, value: Any, data: Mapping[str, Any], /):
        if isinstance(value, str):
            return value
        elif isinstance(value, Mapping):
            return {k: self._fill_value(v, data) for k, v in value.items()}
        elif hasattr(value, "__iter__"):
            return [self._fill_value(v, data) for v in value]
        elif isinstance(value, Operator):
            return value(data)
        else:
            return value

    def _parse_value(self, value, keys: List[str], key: Optional[str] = None):
        if isinstance(value, dict):
            value = {k: self._parse_value(v, keys, key=k) for k, v in value.items()}
        elif isinstance(value, str):
            value = self._parse_string(value, keys, key=key)
        elif isinstance(value, Iterable):
            value = tuple(self._parse_value(v, keys, key=key) for v in value)
        return value

    def _parse_string(self, s: str, keys: List[str], key: Optional[str] = None) -> Union["Operator", str]:
        if not s:
            return s

        bl, br = self.definitions.operator_brackets
        bls, blr = s[0] == bl, s[-1] == br

        if not bls and not blr:
            if s[0] == self.definitions.escape_quote and s[-1] == self.definitions.escape_quote:
                s = s[1:-1]
            return s
        elif not bls or not blr:
            raise ValueError(f'Unbalanced brackets in template: key="{key}", value="{s}"')

        s = s[1:-1]
        counter = 0
        x = 0
        args = []
        quoted = False

        for n, v in enumerate(s):
            if v == self.definitions.escape_quote:
                quoted = not quoted
            elif v == bl and not quoted:
                counter += 1
            elif v == br and not quoted:
                counter -= 1
            if v == self.definitions.operator_delimiter and not quoted:
                if counter == 0:
                    args.append(self._parse_string(s[x:n], keys, key=key))
                    x = n + 1

        s = s[x : len(s)]  # noqa
        if s:
            args.append(self._parse_string(s, keys, key=key))

        if isinstance(args[0], str) and args[0].startswith(self.definitions.operator_sign):
            op = args[0][1:]
            args = args[1:]
        else:
            op = self.definitions.default_operator

        op_obj = self.operators[op](self, tuple(args))
        if type(op_obj) is OperatorSelect:
            keys.extend(arg for arg in args if type(arg) is str)
        return op_obj
