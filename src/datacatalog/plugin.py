import importlib


class Pluggable():
    pass


class Plugin():
    def __init__(self, implementation, config):
        module = '.'.join(implementation.split('.')[:-1])
        class_name = implementation.split('.')[-1]
        impl_class = getattr(importlib.import_module(module), class_name)
        self._implementation = impl_class(config)

    @property
    def implementation(self) -> Pluggable:
        return self._implementation


