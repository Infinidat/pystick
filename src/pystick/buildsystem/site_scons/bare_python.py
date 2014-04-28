import os
from SCons.Script import *


def bare_python_command(env, target, sources, *args, **kwargs):
    if 'ENV' in kwargs:
        os_env = kwargs['ENV']
        del kwargs['ENV']
    else:
        os_env = dict()
    benv = bare_python_env(env, os_env)
    bare_python = benv.Dir('.').File('python_bare{}'.format(env['PROGSUFFIX']))  # TODO: this name is hard-coded.
    if isinstance(sources, tuple):
        sources = list(sources)
    elif not isinstance(sources, list):
        sources = [sources]
    cmd = benv.Command(target, sources, " ".join([bare_python.abspath] + [str(arg) for arg in args]), **kwargs)
    Depends(cmd, bare_python)  # don't include this as a source so it won't get included in $SOURCE.
    return cmd


def add_bare_python_to_env(env):
    env.AddMethod(bare_python_command, "BarePythonCommand")


def bare_python_env(env, os_env):
    # Find where the Python's repository by searching for Lib.
    python_lib_dir = env.Dir("#python/Lib").rentry().abspath
    python_repo_dir = os.path.abspath(os.path.join(python_lib_dir, ".."))

    d = {'PYTHONPATH': 'modules:' + python_lib_dir,
         'PYTHONHOME': python_repo_dir,
         'PATH': env['ENV']['PATH'] + ":{}".format(str(Dir('.')))}
    d.update(os_env)
    env = env.Clone()
    env.Append(ENV=d)
    return env