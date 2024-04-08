[![pypi](https://img.shields.io/pypi/v/template-dict.svg)](https://pypi.python.org/pypi/template-dict/)
[![docs](https://readthedocs.org/projects/template-dict/badge/?version=latest&style=flat)](https://template-dict.readthedocs.io)
[![codecov](https://codecov.io/gh/violet-black/template-dict/graph/badge.svg?token=FEUUMQELFX)](https://codecov.io/gh/violet-black/template-dict)
[![tests](https://github.com/violet-black/template-dict/actions/workflows/tests.yaml/badge.svg)](https://github.com/violet-black/template-dict/actions/workflows/tests.yaml)
[![mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[![python](https://img.shields.io/pypi/pyversions/template-dict.svg)](https://pypi.python.org/pypi/template-dict/)

**template-dict** - JSON compatible Python dictionary templates. You can use them to fill some schema with data
dynamically. Template dicts support nested data, lists. functions and eval of simple Python data types.

# Installation

With pip and python 3.8+:

```bash
pip3 install template-dict
```

# How to use

See the [user guide](https://template-dict.readthedocs.io/guide.html) for more info.

`Template` objects can be used to fill dictionary-like schema with dynamic data.

Note that these are not Jinja templates but rather a tool to manipulate Python data dynamically.
To create a template you must define a schema and then feed it with some data mapping.

```python
from template_dict import Template

t = Template({'value': '[key.nested]'})
t.eval({'key': {'nested': True}})  # -> {'value': True}
```

Template can accept a string or an iterable as a schema.

```python
t = Template(['[name]', '[name]', '[name]'])
t.eval({'name': 'dogs'})  # -> ["dogs", "dogs", "dogs"]
```

You can access template keys before evaluating it.

```python
t = Template({'value': '[key]'})
t.keys  # -> ['key']
```
