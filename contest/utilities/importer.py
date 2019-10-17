import os
import sys
import importlib.util


def import_from_source(path, add_to_modules=False):
    """Imports a Python source file using its path on the system.

    Arguments:
        path (str): path to the source file. may be relative.
        add_to_modules (bool): indicate whether to not to add to sys.modules

    Returns:
        The module object that was imported
    """
    module_name = os.path.splitext(os.path.basename(path))[1]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if add_to_modules:
        sys.modules[module_name] = module
    return module
