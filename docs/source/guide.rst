.. _guide:

User guide
==========

:py:class:`~template_dict.templates.Template`
can be used to fill dictionary-like objects with dynamic data.

Note that these are not Jinja templates but rather a tool for python
data manipulation. To create a template you must define a schema and then feed it with data.

.. code-block:: python

  t = Template({'value': '[key]'})
  t({'key': True})  # -> {'value': True}

Template engine uses a set of various operators and functions to process
dynamic data. See `Operators`_ section for details.

Template can also accept a string or an iterable like `list` or `tuple`.

.. code-block:: python

  t = Template('[fill_this]')
  t({'fill_this': 'dogs'})  # -> "dogs"

Operators
---------

Operators can be used to transform template values before passing them to the schema.

SELECT
______

Set value from a data key. Nested keys are supported.

For your convenience this is a default operator which means that
you don't need to explicitly specify '!s:' after an opening bracket.

.. code-block:: python

    "[key]"
    "[key.nested]"

You can aggregate values from a list in the same way.

.. code-block:: python

  t = Template('[key.nested]')
  t({'key': [{'nested': 1}, {'nested': 2}, {'nested': 3}]})  # -> [1, 2, 3]

If there is no such key in the data, then `KeyError` will be thrown.
However you can provide a second argument as a default value for the key. This
argument will be automatically evaluated using :py:func:`ast.literal_eval` unless
it's an operator.

.. code-block:: python

    "[key:'default']"

FORMAT
______

Format a string from data dict using :py:func:`str.format_map`.

.. code-block:: python

    "[!f:string]"

If a data dict is nested then the flattened version will be used with
all nested keys accessible using `-` (dot is not allowed here due to python
restrictions).

.. code-block:: python

    "[!f:Example string - {key-nested}!]"

Multiple arguments will be joined into a single strings.

.. code-block:: python

  "[!f:key1:key2:key3]"  # -> "key1,key2,key3"

EXEC
____

Execute a function (must be registered) with arguments. Each argument
must be separated by `:`.

.. code-block:: python

    "[!x:<function>:<arg1>:...:<argN>]"

Arguments must respect function input. Arguments are evaluated automatically before passing them to a function.
.. code-block:: python

    "[!x:sum:24:18]"            # -> sum([24, 18])

There a number of standard functions available in :py:obj:`template_dict.FUNCTIONS`.

Combining operators
-------------------

You can use nested brackets to combine multiple operators.
For example you can use a value from the data dict in the `sum` function.

.. code-block:: python

    "[!x:sum:[key1]:[key2]]"  # -> sum([data['key1'], data['key2'])

Multi-level nesting is allowed.

.. code-block:: python

    "[!x:sum:[key1]:[!x:int:[key2]]]"  # -> sum([data['key1'], int(data['key2'])])

Escaping
--------

You can escape things such as brackets with apostrophes.

.. code-block:: python

    "`[escaped]:[value]`"

Examples
--------

You can use templates to automatically fill configuration files on app start
or create objects dynamically using external data.

.. code-block:: python

    import os

    config_template = Template({
      'name': 'my_app',
      'id': '[!x:uuid4],
      'host': '[HOST]',
      'port': '[PORT:80]'
    })

    config_template(os.environ)  # will try to fill host and port values from $HOST and $PORT env vars
