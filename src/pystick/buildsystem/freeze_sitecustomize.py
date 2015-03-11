import imp
import sys

try:
    import os
    freeze_overrides = [s for s in os.environ.get('PYSTICK_PYTHONPATH_FREEZE_OVERRIDES', '').split(':') if s]
except:
    freeze_overrides = []


# The idea is that we put all the frozen modules under either freezer.xxx.yyy.zz or freezer_package.xxx.yy.zz,
# depending on whether the module is a package or not (i.e. __init__). We do it in this hacky way because we're not
# exposed to the size field of a frozen module so we can't know what Python's code knows that a module is a package
# (negative size).
class ModuleImporter(object):

    def is_package(self, fullname):
        return imp.is_frozen('freezer_package.' + fullname)

    def find_module(self, fullname, path=None):
        # Python's default import implementation doesn't handle builtins with '.' in them well, so we handle them here
        # as well.
        # We allow freeze_overrides to give prefixes that although may be frozen we'll skip so they can be found in
        # the PYTHONPATH - this is good for development.
        if (not any(fullname.startswith(override) for override in freeze_overrides)) and \
           (imp.is_frozen('freezer_package.' + fullname) or imp.is_frozen('freezer.' + fullname) or
                (fullname.find('.') != -1 and imp.is_builtin(fullname))):
            return self
        else:
            return None

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass

        if imp.is_builtin(fullname):
            import freeze_external_modules
            try:
                imp.acquire_lock()
                py_package_context = freeze_external_modules.get_py_package_context()
                freeze_external_modules.set_py_package_context(fullname)
                return imp.init_builtin(fullname)
            finally:
                freeze_external_modules.set_py_package_context(py_package_context)
                imp.release_lock()
        else:
            if imp.is_frozen('freezer_package.' + fullname):
                co = imp.get_frozen_object('freezer_package.' + fullname)
                is_package = True
            else:
                co = imp.get_frozen_object("freezer." + fullname)  # This may throw ImportError if not found.
                is_package = False
            try:
                imp.acquire_lock()
                mod = imp.new_module(fullname)
                if '__builtins__' not in mod.__dict__:
                    mod.__dict__['__builtins__'] = __builtins__
                mod.__file__ = "frozen/" + "/".join(fullname.split('.'))
                if is_package:
                    mod.__path__ = [fullname]
                    mod.__file__ = mod.__file__ + "/__init__"
                sys.modules[fullname] = mod
                eval(co, mod.__dict__, mod.__dict__)
                return mod
            finally:
                imp.release_lock()

importer = ModuleImporter()
sys.meta_path.insert(0, importer)

# try:
#     import pkg_resources
#     def distribution_finder()
#     pkg_resources.register_finder(importer, distribution_finder)
# except ImportError:
#     pass
