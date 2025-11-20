# class-properties

[![PyPI](https://img.shields.io/pypi/v/class-properties.svg)](https://pypi.org/project/class-properties/)
[![CI](https://github.com/youruser/class-properties/actions/workflows/ci.yml/badge.svg)](https://github.com/youruser/class-properties/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/youruser/class-properties.svg)](https://codecov.io/gh/youruser/class-properties)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Utilities for **class‑level properties**, mirroring the behavior of `@property`
and `functools.cached_property` but for the class object itself.

Provided decorators:

- `class_property`
- `cached_class_property`
- `threadsafe_cached_class_property`

These work on the **class**, not the instance, and can be accessed through
either.

---

Supports Python 3.11+.

---

## Installation

```bash
pip install class-properties
```

## Overview

Python has `@property` for instance‑level attributes and `@classmethod` for
class‑level methods. The standard library also contains `functools.
cached_property` that caches the result of the initial property access.

This library fills the gaps: you can expose **read‑only, computed attributes on
the class**, and optionally cache the result.

> **⚠️ Critical Note:**  
> Assignment or deletion on the *class* is **unsupported** for any of 
> these variations because Python will destroy the property descriptor.
> Always perform property set/delete operations (if supported) through
> an **instance**, never the class.
> 
> NEVER DO THIS:
>  - `MyClass.prop = 'foo'`
>  - `del MyClass.prop`
---

## `class_property`

A class‑level analogue of `@property`.

- Computed fresh on each access
- Read‑only
- Available via both `MyClass.prop` and `MyClass().prop`

### Example

```python
from class_properties import class_property


class Env:
    @class_property
    def python_path(cls):
        return ':'.join(['/usr/bin', '/usr/local/bin'])


assert Env.python_path.endswith('bin')
assert Env().python_path == Env.python_path
```

**Key point:** No caching; the function executes each time.

---

## `cached_class_property`

A class‑level analogue of `functools.cached_property`.

- First access computes the value and stores it on the class
- Subsequent accesses reuse the cached value
- `instance.prop = value` updates the cached value
- `del instance.prop` invalidates the cached value

### Example

```python
from datetime import datetime

from class_properties import cached_class_property


class App:
    _boot_count = 0

    @cached_class_property
    def boot_time(cls):
        cls._boot_count += 1
        return datetime.now()


# First access computes:
t1 = App.boot_time

# Subsequent accesses read from the class cache:
t2 = App().boot_time
assert t1 is t2

# Override the cached value:
App().boot_time = 'OVERRIDDEN'
assert App.boot_time == 'OVERRIDDEN'

# Invalidate and recompute:
del App().boot_time
t3 = App.boot_time
assert t3 != 'OVERRIDDEN'
```

---

## `threadsafe_cached_class_property`

A thread‑safe variant of `cached_class_property`.

- Wraps all get/set/delete operations in an `RLock`
- Ensures the underlying function is executed **once** even under concurrent
  access
- Behaves identically to `cached_class_property` from the outside

### Example

```python
import time
import threading

from class_properties import threadsafe_cached_class_property


class Expensive:
    @threadsafe_cached_class_property
    def value(cls):
        time.sleep(0.1)
        return 'computed'


results = []


def worker():
    results.append(Expensive.value)


threads = [threading.Thread(target=worker) for _ in range(10)]
[t.start() for t in threads]
[t.join() for t in threads]

assert len(set(results)) == 1  # All threads saw the same cached value
```

---

## Behavior Summary

| Feature                            | `class_property` | `cached_class_property` | `threadsafe_cached_class_property` |
|------------------------------------|------------------|-------------------------|------------------------------------|
| Read access via instance           | Yes              | Yes                     | Yes                                |
| Read access via class              | Yes              | Yes                     | Yes                                |
| Recompute on each access           | Yes              | No                      | No                                 |
| Per‑class caching                  | No               | Yes                     | Yes                                |
| Cache update thread‑safety         | No               | No                      | Yes                                |
| Assign via instance (`x.prop = v`) | Error            | Updates cache           | Updates cache                      |
| Delete via instance (`del x.prop`) | Error            | Invalidates cache       | Invalidates cache                  |

---

## When to Use What

- Use **`class_property`** when you need a derived class attribute with no
  caching.
- Use **`cached_class_property`** when the computation is expensive and
  thread‑safety is not a concern.
- Use **`threadsafe_cached_class_property`** when multiple threads may access
  the property concurrently and the
  underlying computation must execute only once.
