import os.path
import functools
from SCons.Script import *


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


def get_python_modules_configuration(env):
    return dict(
        PYTHON_MODULE_LIBS=env.get('PYTHON_MODULE_LIBS', []),
        SHARED_PYTHON_MODULE_LIBS=env.get('SHARED_PYTHON_MODULE_LIBS', []),
        STATIC_PYTHON_MODULE_LIBS=env.get('STATIC_PYTHON_MODULE_LIBS', []),
        STATIC_PYTHON_MODULE_INIT_FUNCS=env.get('STATIC_PYTHON_MODULE_INIT_FUNCS', []),
        STATIC_PYTHON_MODULE_OBJECTS=env.get('STATIC_PYTHON_MODULE_OBJECTS', [])
    )


def append_python_modules_configuration(env, conf):
    env.Append(PYTHON_MODULE_LIBS=conf['PYTHON_MODULE_LIBS'],
               SHARED_PYTHON_MODULE_LIBS=conf['SHARED_PYTHON_MODULE_LIBS'],
               STATIC_PYTHON_MODULE_LIBS=conf['STATIC_PYTHON_MODULE_LIBS'],
               STATIC_PYTHON_MODULE_INIT_FUNCS=conf['STATIC_PYTHON_MODULE_INIT_FUNCS'],
               STATIC_PYTHON_MODULE_OBJECTS=conf['STATIC_PYTHON_MODULE_OBJECTS'])


def add_module(env, name, is_shared, is_pic, sources, append_env=None, depends=[]):
    if not isinstance(sources, (list, tuple)):
        sources = [sources]

    build_env = env.Clone()
    if append_env:
        build_env.Prepend(**append_env)

    if not is_shared:
        build_env.Append(CPPDEFINES='Py_NO_ENABLE_SHARED')

    obj_builder = build_env.SharedObject if (is_shared or is_pic) else build_env.StaticObject

    # We need to take several things into consideration here:
    # 1. Some C module sources may have the same file name, especially if we're mixing standard C modules with external
    #    ones. We need to avoid object file name conflicts.
    # 2. Some of the standard C modules share some object files. If the modules are statically linked, then a single
    #    object file needs to be shared by all of the modules. If the modules are dynamically linked however, each
    #    module gets its own object file.
    #
    # To do this we do the following:
    # 1. For each dynamically linked module we put all the object files under
    #    {variant_dir}/modules/obj.shared/{module_name}/{path_to_source}.
    #    This ensures that two dynamically linked modules don't have name conflicts with their sources since the
    #    module name must be unique and that a source that's shared between several shared modules will get built
    #    per-module, so it can receive different compilation flags per module.
    # 2. For each statically linked module we put all the object files under
    #    {variant_dir}/modules/obj.static/{path_to_source}.
    #    This means that if two modules share the same source file only a single object file is used (e.g. timemodule.c
    #    in Python's standard C modules). As a precaution we try to make sure that the same compilation flags are given
    #    by all modules sharing the same object file.
    def source_to_obj_path(source):
        drive_part, path_part = os.path.splitdrive(env.File(source).abspath)  # on Windows, get the drive first
        drive_part = drive_part.replace(':', '')  # remove ':' from the drive
        path_part, _ = os.path.splitext(path_part)  # Remove the extension (i.e. '.c')
        path_part, fname = os.path.split(path_part)

        obj_fname = "{}{}{}".format(env['SHOBJPREFIX' if is_shared else 'OBJPREFIX'], fname,
                                    env['SHOBJSUFFIX' if is_shared else 'OBJSUFFIX'])

        # remove empty path parts
        parts = filter(bool, ('modules', 'obj.{}'.format('shared' if is_shared else 'static'), drive_part, path_part,
                              obj_fname))
        # remove leading path separators from components
        parts = [p[len(os.path.sep):] if p.startswith(os.path.sep) else p for p in parts]
        return os.path.sep.join(parts)

    objects = [obj_builder(target=source_to_obj_path(source), source=source) for source in sources]

    if is_shared:
        build_env.Replace(SHLIBPREFIX='')  # shared lib modules don't need a 'lib' prefix, FIXME also in OSX?
        mod = build_env.SharedLibrary(target=env.Dir('modules').File(name), source=objects)
        env.Append(SHARED_PYTHON_MODULE_LIBS=[mod])
    else:
        mod = build_env.StaticLibrary(target=env.Dir('modules').File(env['LIBPREFIX'] + name + env['LIBSUFFIX']),
                                      source=objects)
        env.Append(STATIC_PYTHON_MODULE_LIBS=[mod])
        env.Append(STATIC_PYTHON_MODULE_INIT_FUNCS=[name])
        # We only add to STATIC_PYTHON_MODULE_OBJECTS unique object files (ones that weren't added by other libs)
        prev_objs = set(str(n) for n in env.get('STATIC_PYTHON_MODULE_OBJECTS', []))
        new_objs = [obj for obj in objects if str(obj) not in prev_objs]
        env.Append(STATIC_PYTHON_MODULE_OBJECTS=new_objs)
    env.Append(PYTHON_MODULE_LIBS=[mod])


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
        add_module(env, name, is_shared, is_pic, sources, append_env, depends)


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
    env.AddMethod(get_python_modules_configuration, "GetPythonModulesConfiguration")
    env.AddMethod(append_python_modules_configuration, "AppendPythonModulesConfiguration")