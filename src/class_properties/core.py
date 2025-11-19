from __future__ import annotations
import threading
from typing import Callable, Generic, Optional, Type, TypeVar
T=TypeVar("T"); R=TypeVar("R")

class class_property(property):
    def __get__(self, instance, owner=None):
        if owner is None: raise RuntimeError("class_property accessed with no owner")
        return self.fget(owner)

class cached_class_property(Generic[T,R]):
    __slots__=("func","_cache_name")
    def __init__(self, func): self.func=func; self._cache_name=f"__cachedclassprop_{func.__name__}"
    def __set_name__(self, owner,name): return None
    def __get__(self, instance, owner=None):
        if owner is None: raise RuntimeError("cached_class_property accessed with no owner")
        try: return owner.__dict__[self._cache_name]
        except KeyError:
            v=self.func(owner); setattr(owner,self._cache_name,v); return v
    def invalidate(self, owner):
        if self._cache_name in owner.__dict__: delattr(owner,self._cache_name)
    def set(self, owner,value): setattr(owner,self._cache_name,value)

class threadsafe_cached_class_property(cached_class_property[T,R]):
    __slots__=("_lock",)
    def __init__(self, func): super().__init__(func); self._lock=threading.RLock()
    def __get__(self, instance, owner=None):
        if owner is None: raise RuntimeError("cached_class_property accessed with no owner")
        try: return owner.__dict__[self._cache_name]
        except KeyError: pass
        with self._lock:
            try: return owner.__dict__[self._cache_name]
            except KeyError:
                v=self.func(owner); setattr(owner,self._cache_name,v); return v
