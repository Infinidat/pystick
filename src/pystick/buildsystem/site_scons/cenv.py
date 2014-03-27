from contextlib import contextmanager
from SCons.Script import *

__env_stack = []
__variables = None

def init(env):
    __env_stack.append(env)
    return env

def push(**kwargs):
    env = current().Clone(**kwargs)
    __env_stack.append(env)
    return env


def pop():
    return __env_stack.pop(-1)


def current():
    return __env_stack[-1]


@contextmanager
def context(**kwargs):
    new_env = push(**kwargs)
    try:
        yield new_env
    finally:
        pop()


def init_global_variables(*args, **kwargs):
    global __variables
    __variables = Variables(*args, **kwargs)
    return __variables


def get_global_variables():
    global __variables
    if not __variables:
        __variables = Variables()
    return __variables