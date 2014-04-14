import imp
import sys

class ModuleImporter(object):
    def find_module(self, fullname, path=None):
        try:
            imp.get_frozen_object("freezer." + fullname)
            return self
        except ImportError:
            return None

    def load_module(self, fullname):
        try:
            return sys.modules[fullname]
        except KeyError:
            pass

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