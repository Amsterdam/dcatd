import importlib


class Pluggable(object):
    pass


class Plugin(object):
    def __init__(self, implementation: str, config):
        # language=rst
        """Constructor.

        Args:
            implementation: class name, with its full module path, eg.
                ``'my.module.MyClass'``
            config: TODO: document

        """
        module = '.'.join(implementation.split('.')[:-1])
        class_name = implementation.split('.')[-1]
        impl_class = getattr(importlib.import_module(module), class_name)
        self._implementation = impl_class(config)

    @property
    def implementation(self) -> Pluggable:
        return self._implementation
