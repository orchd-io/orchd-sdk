import sys
import importlib

from typing import Any


def import_class(class_: str) -> Any:
    """Imports a class described in the given String"""
    class_parts = class_.split('.')
    class_name = class_parts.pop()
    module_name = '.'.join(class_parts)

    if module_name not in sys.modules:
        importlib.import_module(module_name)
    Class = getattr(sys.modules.get(module_name), class_name)

    return Class
