from . import arrayable_class

def printf(text, *formatter):
    print(str(text) % formatter)

@arrayable_class.arrayable
class char(object):
    def __init__(self, value):
        try:
            self.value = chr(value)
        except Exception:
            if len(str(value)) != 1:
                raise ValueError("Invalid byte. ")
            self.value = str(value)
    def __str__(self):
        return self.value
    def __repr__(self):
        return f"{self.__class__}({self.value})"
    def __eq__(self,o):
        return self.value == o.value
    def __lt__(self,o):
        return ord(self.value) < ord(o.value)
    def __gt__(self,o):
        return ord(self.value) > ord(o.value)
    def __le__(self,o):
        return ord(self.value) <= ord(o.value)
    def __ge__(self,o):
        return ord(self.value) >= ord(o.value)
    def __int__(self):
        return ord(self.value)
    # 可选：支持 ord(c) 直接返回 int
    def __index__(self):
        return self.__int__()
    def __setattr__(self, key, value):
        if hasattr(self, 'value'):
            raise TypeError("'char' object does not support item assignment")
        super().__setattr__(key, value)

class struct(object):
    def __init__(self, **kwargs):
        # 定义允许的属性及其类型
        self._allowed_attributes = {key: type(value) for key, value in kwargs.items()}
        # 设置初始属性值
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        # 检查是否是私有属性或已定义的属性
        if key.startswith("_") or key in self._allowed_attributes:
            # 检查类型是否匹配
            if key in self._allowed_attributes and not isinstance(value, self._allowed_attributes[key]):
                raise TypeError(f"Attribute '{key}' must be of type {self._allowed_attributes[key].__name__}")
            super().__setattr__(key, value)
        else:
            # 防止动态添加新属性
            raise AttributeError(f"Cannot add new attribute '{key}' dynamically")

