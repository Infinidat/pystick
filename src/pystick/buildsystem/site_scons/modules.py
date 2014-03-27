from SCons.Script import *
from cenv import get_global_variables

def name_to_mangled(name):
    from utils import mangle_name
    return mangle_name(name).upper()


def required_libs_predicate(env, *libs):
    return all(env.get('HAVE_LIB{}'.format(lib.upper()), False) for lib in libs)


def are_python_modules_shared(env):
    if 'SHARED_PYTHON_MODULES' in env:
        return env['SHARED_PYTHON_MODULES']
    elif 'STATIC_PYTHON_MODULES' in env:
        return not env['STATIC_PYTHON_MODULES']
    return True


def add_module(env, name, is_shared, is_pic, sources, append_env=None, depends=[]):
    if not isinstance(sources, (list, tuple)):
        sources = [sources]

    build_env = env.Clone()
    if append_env:
        build_env.Append(**append_env)
    obj_builder = build_env.SharedObject if is_shared or is_pic else build_env.StaticObject
    objects = [obj_builder(source) for source in sources]
    if is_shared:
        build_env.Replace(SHLIBPREFIX='')  # shared lib modules don't need a 'lib' prefix
        mod = build_env.SharedLibrary(Dir('modules').File(name), objects)
    else:
        mod = build_env.StaticLibrary(Dir('modules').File(name), objects)
        env.Append(STATIC_PYTHON_MODULE_INIT_FUNCS=[name])
        env.Append(STATIC_PYTHON_MODULES=[mod])
        env.Append(STATIC_PYTHON_MODULE_OBJECTS=objects)
    env.Append(PYTHON_MODULES=[mod])


def add_python_module(env, name, sources, requirements=True, append_env=None, depends=[]):
    mangled_name = name_to_mangled(name)
    if not env.get('WITH_PYTHON_MODULE_{}'.format(mangled_name)):
        return

    per_module_is_shared_env_var = 'SHARED_PYTHON_MODULE_{}'.format(mangled_name)
    per_module_is_static_env_var = 'STATIC_PYTHON_MODULE_{}'.format(mangled_name)

    if per_module_is_shared_env_var in env:
        is_shared = env[per_module_is_shared_env_var]
    elif per_module_is_static_env_var in env:
        is_shared = not env[per_module_is_static_env_var]
    else:
        is_shared = are_python_modules_shared(env)

    per_module_is_pic_env_var = 'PIC_PYTHON_MODULE_{}'.format(mangled_name)
    if per_module_is_pic_env_var in env:
        is_pic = env[per_module_is_pic_env_var] or is_shared
    elif 'PIC_PYTHON_MODULES' in env:
        is_pic = env['PIC_PYTHON_MODULES'] or is_shared
    else:
        is_pic = is_shared

    if requirements:
        add_module(env, name, is_shared, is_pic, sources, append_env)


def add_python_module_vars(env, vars, name, enabled=True, can_be_shared=True, requires_desc=None):
    mangled_name = name_to_mangled(name)

    enable_message = 'Set to enable module {}'.format(name)
    if requires_desc:
        enable_message += ", requires " + requires_desc

    vars.AddVariables(
        BoolVariable('WITH_PYTHON_MODULE_{}'.format(mangled_name), enable_message, enabled),
        BoolVariable('PIC_PYTHON_MODULE_{}'.format(mangled_name), 'Set to enable -fPIC in module {}'.format(name),
                     False),
    )

    if can_be_shared:
        vars.AddVariables(
            BoolVariable('STATIC_PYTHON_MODULE_{}'.format(mangled_name),
                         'Set to explicitly build module {} as static'.format(name), False),
            BoolVariable('SHARED_PYTHON_MODULE_{}'.format(mangled_name),
                         'Set to explicitly build module {} as shared'.format(name), False)
        )
    else:
        env['STATIC_PYTHON_MODULE_{}'.format(mangled_name)] = True
        env['SHARED_PYTHON_MODULE_{}'.format(mangled_name)] = False


def add_python_module_funcs_to_env(env):
    env.SetDefault(STATIC_PYTHON_MODULE_INIT_FUNCS=[])
    env.SetDefault(PYTHON_MODULES=[])
    env.AddMethod(add_python_module, "AddPythonModule")
    env.AddMethod(required_libs_predicate, "RequiredLibsPredicate")
    env.AddMethod(add_python_module_vars, "AddPythonModuleVars")
