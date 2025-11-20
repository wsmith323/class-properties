from __future__ import annotations

import threading
from typing import Generic, TypeVar

T = TypeVar('T')
R = TypeVar('R')


class class_property(Generic[R]):
    """Read-only, class-level analogue of @property.

    Access via either the class or an instance:

        class C:
            _threshold = 10

            @class_property
            def threshold(cls):
                return cls._threshold

        C.threshold       # 10
        C().threshold     # 10

    Any attempt to assign or delete via an instance is rejected:

        C().threshold = 20   # AttributeError
        del C().threshold    # AttributeError

    Note:
        - Assignment on the *class* (``MyClass.prop = value``) will overwrite
          this descriptor at the language level and is not supported.
        - Likewise, deleting the attribute on the class (``del MyClass.prop``) removes
          this descriptor entirely at the language level and is unsupported.
    """

    __slots__ = ('fget', '__doc__', 'name')

    def __init__(self, fget, doc=None):
        if fget is None:
            raise TypeError('fget must not be None')
        self.fget = fget
        self.__doc__ = doc or getattr(fget, '__doc__', None)
        self.name: str | None = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        cls = owner or (type(instance) if instance is not None else None)
        if cls is None:
            raise RuntimeError(f"class property '{self.name}' accessed with no owner")
        return self.fget(cls)

    def __set__(self, instance, value):
        raise AttributeError(
            f"class property '{self.name}' is read-only",
        )

    def __delete__(self, instance):
        raise AttributeError(
            f"class property '{self.name}' is read-only",
        )


class cached_class_property(Generic[T, R]):
    """Class-level analogue of functools.cached_property.

    - Value is cached per owner class.
    - First access computes and caches ``func(cls)`` on that class.
    - ``del instance.prop`` invalidates the cache for the owner class; the
      next access recomputes and recaches it.
    - ``instance.prop = value`` updates the cached value for the owner class.

    Note:
        - Assignment on the *class* (``MyClass.prop = value``) will overwrite
          this descriptor at the language level and is not supported.
        - Likewise, deleting the attribute on the class (``del MyClass.prop``) removes
          this descriptor entirely at the language level and is unsupported.
    """

    __slots__ = ('func', '_cache_name', 'name')

    def __init__(self, func):
        self.func = func
        self._cache_name = f'__cachedclassprop_{func.__name__}'
        self.name: str | None = None

    def __set_name__(self, owner, name):
        self.name = name

    def _get_owner(self, instance, owner):
        if owner is not None:
            return owner
        if instance is not None:
            return type(instance)
        return None

    def __get__(self, instance, owner=None):
        cls = self._get_owner(instance, owner)
        if cls is None:
            raise RuntimeError('cached_class_property accessed with no owner')
        try:
            return cls.__dict__[self._cache_name]
        except KeyError:
            value = self.func(cls)
            setattr(cls, self._cache_name, value)
            return value

    def __set__(self, instance, value):
        """Directly update the cached value via an instance.

        ``instance.prop = value`` updates the cached value for the owner class.
        ``MyClass.prop = value`` overwrites the descriptor and must be avoided.
        """
        if instance is None:
            raise AttributeError(
                f"cached_class_property '{self.name}' cannot be set on the class; "
                'set it via an instance or explicit API instead',
            )
        cls = type(instance)
        setattr(cls, self._cache_name, value)

    def __delete__(self, instance):
        """Invalidate the cached value via an instance.

        ``del instance.prop`` removes the cached value for the owner class; the next
        access recomputes and recaches it.
        """
        if instance is None:
            raise AttributeError(
                f"cached_class_property '{self.name}' cannot be deleted on the class; "
                'delete it via an instance or explicit API instead',
            )
        cls = type(instance)
        try:
            delattr(cls, self._cache_name)
        except AttributeError:
            # Already not cached; no-op for idempotence.
            pass

    def invalidate(self, owner):
        """Explicitly invalidate the cached value for a given owner class."""
        try:
            delattr(owner, self._cache_name)
        except AttributeError:
            pass

    def set(self, owner, value):
        """Explicitly set the cached value for a given owner class."""
        setattr(owner, self._cache_name, value)


class threadsafe_cached_class_property(cached_class_property[T, R]):
    """Thread-safe variant of cached_class_property.

    Uses an RLock around get, set, delete, and the explicit helper methods. This prevents race conditions on cache
    access but may incur a small performance penalty. Use only if you absolutely require a single getter execution within
    a multithreaded environment.
    """

    __slots__ = ('_lock',)

    def __init__(self, func):
        super().__init__(func)
        self._lock = threading.RLock()

    def __get__(self, instance, owner=None):
        cls = self._get_owner(instance, owner)
        if cls is None:
            raise RuntimeError('cached_class_property accessed with no owner')
        try:
            return cls.__dict__[self._cache_name]
        except KeyError:
            with self._lock:
                try:
                    return cls.__dict__[self._cache_name]
                except KeyError:
                    value = self.func(cls)
                    setattr(cls, self._cache_name, value)
                    return value

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError(
                f"cached_class_property '{self.name}' cannot be set on the class; "
                'set it via an instance or explicit API instead',
            )
        cls = type(instance)
        with self._lock:
            setattr(cls, self._cache_name, value)

    def __delete__(self, instance):
        if instance is None:
            raise AttributeError(
                f"cached_class_property '{self.name}' cannot be deleted on the class; "
                'delete it via an instance or explicit API instead',
            )
        cls = type(instance)
        with self._lock:
            try:
                delattr(cls, self._cache_name)
            except AttributeError:
                pass

    def invalidate(self, owner):
        """Thread-safe invalidation of the cached value for a given owner class."""
        with self._lock:
            try:
                delattr(owner, self._cache_name)
            except AttributeError:
                pass

    def set(self, owner, value):
        """Thread-safe setter for the cached value for a given owner class."""
        with self._lock:
            setattr(owner, self._cache_name, value)
