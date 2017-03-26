# -*- python -*-
import sys
import marshal


def main():
    if len(sys.argv) != 6:
        print("usage: compile_bytecode.py src target name filename is_package")
        return
    src_path, target_path, module_name, filename, is_package = sys.argv[1:]
    mangled_module_name = module_name.replace('.', '__').replace('-', '_').replace('(', '_').replace(')', '_').replace(' ', '_')
    is_package = is_package.lower() in ('t', 'true', '1', 'yes')

    print("src_path={}, target_path={}".format(src_path, target_path))
    with open(src_path, "r") as input:
        source = input.read()
        if source.find('\n') != -1 and source.startswith('#') and 'coding' in source[:source.index('\n')]:
            source = source[source.index('\n'):]
        with open(target_path, "w") as output:
            if src_path.endswith(".py"):
                try:
                    code_obj = compile(source, filename, 'exec', 0, 1)
                    code = marshal.dumps(code_obj)
                except LookupError:
                    sys.stderr.write("WARNING: {} failed on encoding error, writing an empty (invalid) file.\n".format(src_path))
                    code = ""
                except SyntaxError:
                    sys.stderr.write("WARNING: {} failed on syntax error, writing an empty (invalid) file.\n".format(src_path))
                    code = ""
            else:
                # assume .pyc/.pyo
                code = code[8:]  # skip magic + timestamp
            size = len(code) * (-1 if is_package else 1)
            output.write("/* Autogenerated by compile_bytecode.py */\n")
            output.write("/* The following comments are used by automatic tools, so tread carefully here. */\n")
            output.write("/* Module: %s */\n" % module_name)
            output.write("/* Code: _FreezeM%s */\n" % mangled_module_name)
            output.write("/* Size: %s */\n" % size)
            output.write("/* File: %s */\n" % filename)
            output.write("/* Is Package: %s */\n" % is_package)
            output.write("unsigned char _FreezeM%s[] = {\n" % mangled_module_name)
            for i in range(0, len(code), 32):
                for c in code[i:i + 32]:
                    output.write("{:#04x}, ".format(ord(c)))
                output.write("\n")
            output.write("};\n")

if __name__ == "__main__":
    main()
