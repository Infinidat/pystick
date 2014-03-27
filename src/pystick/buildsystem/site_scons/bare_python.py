from SCons.Script import *


def bare_python_command(env, target, sources, *args, **kwargs):
    benv = bare_python_env(env)
    bare_python = benv.Dir('.').File('python.bare')  # TODO: this name is hard-coded.
    if isinstance(sources, tuple):
        sources = list(sources)
    elif not isinstance(sources, list):
        sources = [sources]
    cmd = benv.Command(target, sources, " ".join([bare_python.abspath] + [str(arg) for arg in args]), **kwargs)
    Depends(cmd, bare_python)  # don't include this as a source so it won't get included in $SOURCE.
    return cmd


def add_bare_python_to_env(env):
    env.AddMethod(bare_python_command, "BarePythonCommand")


def bare_python_env(env):
    # Find where the Python's repository by searching for Lib.
    python_repo_dir = [d for d in Dir('Lib').get_all_rdirs() if d.exists()][0].Dir('..').abspath

    env = env.Clone()
    # We set _PYTHON_HOST_PLATFORM to 'platform' so it'll be easier for us to tell where _sysconfigdata.py will be
    # generated and not having to run python to do it. Also, when we'll do cross-compile we'll have to do that anyhow.
    env.Append(ENV={'_PYTHON_HOST_PLATFORM': 'platform',
                    'PYTHONPATH': 'modules:' + "{}/Lib".format(python_repo_dir),
                    'PYTHONHOME': python_repo_dir,
                    'PATH': env['ENV']['PATH'] + ":{}".format(str(Dir('.')))})
    return env