import os
import sys
import pkg_resources


def relative_path_to_abspath(path):
    return os.path.abspath(path) if not os.path.isabs(path) else path


def fix_assign_flag(flag):
    if flag.find('=') != -1:
        key, val = flag.split('=', 1)
        if key in ('BUILD_PATH', 'PYTHON_SOURCE_PATH', 'EXTERNAL_C_MODULES_FILE', 'EXTERNAL_PY_MODULES_FILE',
                   '--defaultenv'):
            abspath = relative_path_to_abspath(val)
            if abspath != val:
                print("setting {} to {}".format(key, abspath))
            return "{}={}".format(key, abspath)
    return flag


def fix_flags(flags):
    args = [fix_assign_flag(flag) for flag in flags]
    for i, arg in enumerate(args):
        if arg == '--defaultenv':
            abspath = relative_path_to_abspath(args[i + 1])
            print("setting {} to {}".format(args[i + 1], abspath))
            args[i + 1] = abspath
            break
    return args

def main(argv=sys.argv[1:]):
    sconsflags = os.environ.get('SCONSFLAGS', '')
    if sconsflags:
        os.environ.set('SCONSFLAGS', fix_flags(sconsflags.split()).join(" "))

    sys.argv[1:] = fix_flags(argv)

    sys.argv.append('--warn=no-duplicate-environment')

    buildsystem_path = pkg_resources.resource_filename(__name__, "buildsystem")
    os.chdir(buildsystem_path)
    import SCons.Script
    SCons.Script.main()
