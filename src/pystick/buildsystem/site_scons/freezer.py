# Note: this module assumes add_bare_python_to_env was called for any env passed to it.
import re
import os
import marshal
import compile_bytecode
from SCons.Script import *


def no_freeze_conflict_if_equal(full_module_name, path_a, path_b):
    with open(path_a, "r") as a_f:
        a = marshal.dumps(compile(a_f.read(), "<string>", 'exec', 0, 1))
    with open(path_b, "r") as b_f:
        b = marshal.dumps(compile(b_f.read(), "<string>", 'exec', 0, 1))
    if a != b:
        raise Exception("module {} has two different sources: {} and {}".format(full_module_name, path_a, path_b))
    return False


def freeze_file(env, target_path, path, namespace, module_name, frozen_modules, depends=[], conflict_resolver=no_freeze_conflict_if_equal):
    if module_name == '__init__':
        full_module_name = namespace
        is_package = True
    else:
        full_module_name = "{}.{}".format(namespace, module_name) if namespace else module_name
        is_package = False

    target_file_name = full_module_name.replace('.', '__').replace('(', '_').replace(')', '_').replace(' ', '_')
    target = target_path.File("{}.c".format(target_file_name))
    add_module = True
    if full_module_name in frozen_modules:
        if not conflict_resolver(full_module_name, frozen_modules[full_module_name], path):
            add_module = False
    if add_module:
        frozen_modules[full_module_name] = path
        # Can't use $SOURCE here because scons converts the absolute path into a relative path which doesn't work
        # because we're running python.bare from the build directory.
        return env.BarePythonCommand(target, path,
                                     "-S", compile_bytecode.__file__, "$SOURCE", "$TARGET", full_module_name, path, is_package)
    else:
        return None


def freeze_dir(env, target_path, path, root_path=None, namespace=None, exclude_list=[], include_list=[], recurse=True,
               frozen_modules=None, conflict_resolver=no_freeze_conflict_if_equal):
    result = []
    if root_path is None:
        root_path = path
    if frozen_modules is None:
        frozen_modules = dict()

    frozen_names = set()
    for name in os.listdir(path):
        full_path = os.path.join(path, name)
        relative_path = full_path[len(os.path.commonprefix([root_path, full_path])):]
        if relative_path.startswith(os.path.sep):
            relative_path = relative_path[1:]

        # print("freeze_dir: considering {} (root_path={}, path={})".format(relative_path, root_path, full_path))
        if any(re.search(r, relative_path) for r in exclude_list) \
            and not any(re.search(r, relative_path) for r in include_list):
            continue

        if os.path.isdir(full_path) and recurse:
            child_ns = ".".join(s for s in (namespace, name) if s)
            result.extend(freeze_dir(env, target_path, full_path, root_path, child_ns, exclude_list, include_list,
                                     recurse, frozen_modules, conflict_resolver))
        else:
            base_name, ext = os.path.splitext(name)
            target = None
            if ext in (".py", ".pyc", ".pyo"):
                if base_name not in frozen_names:
                    # We prefer to get the .py if available so we'll compile it with our version of Python
                    if ext == ".py":
                        target = freeze_file(env, target_path, full_path, namespace, base_name, frozen_modules,
                                             conflict_resolver)
                    elif not os.path.exists(os.path.join(path, "{}.py".format(base_name))):
                        target = freeze_file(env, target_path, full_path, namespace, base_name, frozen_modules,
                                             conflict_resolver)
            if target:
                result.append(target)
    return result
