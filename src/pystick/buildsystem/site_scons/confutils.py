import os
import stat
import re
import types

def convert_header_to_include(header):
    if isinstance(header, types.StringTypes):
        header = [header]
    return "\n".join("#include <{}>".format(h) for h in header)


def symbol_to_define(sym, prefix='HAVE_', suffix='', irregular_symbols=dict()):
    return prefix + irregular_symbols.get(sym, re.sub(r'[\. /]', '_', sym.upper())) + suffix


def check_device_file(context, dev_file):
    context.Message("Checking if {} exists in is a device file... ".format(dev_file))
    if os.path.exists(dev_file):
        mode = os.stat(dev_file).st_mode
        if stat.S_ISCHR(mode) or stat.S_ISBLK(mode):
            context.Result(True)
            return True
    context.Result(False)
    return False


def check_c_runs(context, message, code):
    context.Message(message)
    result, output = context.TryRun(code, ".c")
    context.Result(result == 1)
    return result == 1


def check_c_compiles(context, message, code):
    context.Message(message)
    result = context.TryCompile(code, ".c")
    context.Result(result == 1)
    return result == 1


def check_c_links(context, message, code):
    context.Message(message)
    result = context.TryLink(code, ".c")
    context.Result(result == 1)
    return result == 1


def check_c_struct_member(context, header, type_name, member):
    code = """
%(header)s
int main() {
    struct %(type_name)s var;
    return var.%(member)s ? 0 : 0;
}
"""
    return check_c_runs(context, 'Checking if C struct {} has member {}... '.format(type_name, member),
                        code % dict(header=convert_header_to_include(header), type_name=type_name, member=member))


def check_symbol_declaration(config, sym_name, lib_name=''):
    code = """
/* Override any GCC internal prototype to avoid an error.
   Use char because int might match the return type of a GCC
   builtin and then its argument prototype would still apply.  */
#ifdef __cplusplus
extern "C"
#endif
char %(sym_name)s();
int main() {
    return %(sym_name)s();
}
"""
    if lib_name:
        lib_name = lib_name + ' '
    return config.CheckCLinks('Checking for {}{}()... '.format(lib_name, sym_name), code % dict(sym_name=sym_name))


def check_ar_supports_response_file(context):
    import tempfile
    import os
    import SCons

    context.Message("Checking if AR supports response file (@)... ")

    env = context.sconf.env

    text_fd, text_path = tempfile.mkstemp()
    os.close(text_fd)

    rsp_fd, rsp_path = tempfile.mkstemp()
    os.write(rsp_fd, text_path)
    os.close(rsp_fd)

    ar_path = tempfile.mktemp(suffix='.ar')

    new_ar_command = env['ARCOM'].replace('$SOURCES', '@$_RSP_FILE')
    action = SCons.Action.CommandAction(new_ar_command)

    try:
        result = action.execute(ar_path, text_path, env.Clone(_RSP_FILE=rsp_path))
        context.Result(result == 0)
        return result == 0
    finally:
        os.unlink(rsp_path)
        os.unlink(text_path)
        if os.path.exists(ar_path):
            os.unlink(ar_path)


def get_custom_tests_dict():
    return dict(CheckCStructMember=check_c_struct_member,
                CheckCRuns=check_c_runs,
                CheckCCompiles=check_c_compiles,
                CheckCLinks=check_c_links,
                CheckDeviceFile=check_device_file,
                CheckARResponseFile=check_ar_supports_response_file)