# class-properties

[![PyPI](https://img.shields.io/pypi/v/class-properties.svg)](https://pypi.org/project/class-properties/)
[![CI](https://github.com/youruser/class-properties/actions/workflows/ci.yml/badge.svg)](https://github.com/youruser/class-properties/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/youruser/class-properties.svg)](https://codecov.io/gh/youruser/class-properties)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Utilities for **class-level properties**:

- `class_property`
- `cached_class_property`
- `threadsafe_cached_class_property`

They work like `@property`, but for the **class itself** instead of its instances.

---
Supports Python 3.11+.
---

## Quick start

```bash
pip install class-properties
```

## Usage

```python
import os
from datetime import date

from class_properties import class_property, cached_class_property

class Config:
    name: str = 'foo'
    version: str = '1.0'

    @class_property
    def copyright(cls):
        # Some inputs can change over time (e.g., the current year),
        # so we must recompute the result every time.
        return f'\u00A9 {date.today().year} {cls.name}, All rights reserved.'
    
    @cached_class_property
    def version_tag(cls):
        # The inputs don't change, so we can cache the result.
        # NOTE: This is a contrived example. In real life, this
        #       would be a more expensive operation.
        return f'{cls.name}-{cls.version}'
```
## Class-level property

### `class_property`: computed on every access

`cached_class_property` behaves like the builtin `property`, but is for the class.

Use this when you want a property that:
- Is defined for the class, with the class passed as the first argument to the getter.
- Is recomputed every time it’s accessed
 
A `class_property` can be accessed on both the class and instances.

## Class-level cached property

### `cached_class_property`: computed once per class

`cached_class_property` behaves like `functools.cached_property`, but is for the class.

Use this when you want a class property where:
- The first access computes the value and stores it on the class.
- Subsequent accesses reuse the cached value.

Like `class_property`, a `cached_class_property` can be accessed on both the class and instances.
