import re
from SCons.Script import *


def is_building():
    return not GetOption('help')


def mangle_name(name):
    return re.sub(r'[ -()]', '_', name).replace('.', '__')
