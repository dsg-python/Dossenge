# from abc import ABC, abstractmethod
undefined = type('undefined', (object, ), {})()

class array(object):
    def __init__(self, size, typ, *, default_factory=None):
        if not isinstance(size, int) or size < 0:
            raise ValueError("size must be a non-negative integer")
        self.size = size
        self.typ = typ
        self._data = [None] * size if default_factory is None else [default_factory() for _ in range(size)]

    # ---------- 读 ----------
    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self._data[i] for i in self._slice_indices(index)]
        # 普通下标
        idx = self._norm_index(index)
        return self._data[idx]

    # ---------- 写 ----------
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            indices = self._slice_indices(index)
            if len(indices) != len(value):
                raise ValueError("attempt to assign sequence of size "
                                 f"{len(value)} to slice of size {len(indices)}")
            for i, v in zip(indices, value):
                self._validate_and_set(i, v)
        else:
            idx = self._norm_index(index)
            self._validate_and_set(idx, value)

    # ---------- 内部工具 ----------
    def _norm_index(self, idx):
        """把任意整数下标转成 0<=idx<size"""
        if idx < 0:
            idx += self.size
        if not 0 <= idx < self.size:
            raise IndexError("array index out of range")
        return idx

    def _slice_indices(self, s):
        """返回 slice 对应的真实下标列表，支持负步长"""
        if s.step is None or s.step > 0:
            base = range(self.size)
        else:                       # 负步长
            base = range(self.size - 1, -1, -1)
        return list(base)[s]

    def _validate_and_set(self, idx, val):
        if not isinstance(val, self.typ):
            raise TypeError(f"Expected {self.typ.__name__}, got {type(val).__name__}")
        self._data[idx] = val

    # ---------- 其余保持原样 ---------

    def __len__(self):
        return self.size

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return f"array(size={self.size}, typ={self.typ.__name__})"

    def __str__(self):
        return f"{self.typ.__name__}[{self.size}]: {self._data}"
    
    def printchar(self):
        if self.typ is char:
            for i in self._data:
                print(i, end="")
        else:
            raise TypeError("printchar(): self.typ must be char")


class arrayable_class_meta(type):
    def __getitem__(cls, size):
        factory = getattr(cls, "__array_default_factory__", None)
        return array(size=size, typ=cls, default_factory=factory)

class arrayable_class(metaclass=arrayable_class_meta):
    pass
    
def arrayable(cls):
    """装饰器：把 cls 的元类换成 arrayable_class_meta"""
    # 动态创建一个新元类，复用已有逻辑
    new_meta = type('arrayable_meta_for_' + cls.__name__,
                    (arrayable_class_meta,), {})
    # 用新元类重新生成类
    return new_meta(cls.__name__, cls.__bases__, dict(cls.__dict__))