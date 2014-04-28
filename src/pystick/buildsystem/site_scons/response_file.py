def gen_rsp_file(target, source, env):
    with open(target[0].abspath, "w") as f:
        for s in source:
            f.write("{}\n".format(s.abspath))
