from class_properties import class_property, cached_class_property

class Example:
    value=2
    @class_property
    def doubled(cls): return cls.value*2

def test_cp():
    assert Example.doubled==4
    assert Example().doubled==4

class Cached:
    counter=0
    @cached_class_property
    def val(cls): cls.counter+=1; return cls.counter

def test_cached():
    assert Cached.val==1
    assert Cached.val==1
