import imp
import sys

class ModuleImporter(object):
    def find_module(self, fullname, path=None):
        try:
            imp.get_frozen_object("freezer." + fullname)
            return self
        except ImportError:
            if fullname.find('.') != -1 and imp.is_builtin(fullname):
                # Python's default import implementation doesn't handle builtins with '.' in them well.
                return self
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
            co = imp.get_frozen_object("freezer." + fullname)
            try:
                imp.acquire_lock()
                mod = imp.new_module(fullname)
                if '__builtins__' not in mod.__dict__:
                    mod.__dict__['__builtins__'] = __builtins__
                mod.__path__ = fullname
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