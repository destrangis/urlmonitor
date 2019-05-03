
def action_object(name, arglst, url, content, variables, log):
    log.info("{} not yet implemented.".format(name))
    log.info("Would run script '{}'".format(arglst[0]))
    log.info("\twith args: {}".format(", ".join(arglst[1:])))
    return { name + "_return_code": 0, name + "_stdout": "" }
