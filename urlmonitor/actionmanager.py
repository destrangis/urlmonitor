
class ActionManager:

    def __init__(self):
        self.actions = {}

    def define_action(self, name, func):
        self.actions[name] = func

    def get_action(self, name):
        return self.actions.get(name, noaction)

    def run(self, name, arglst, url, content, variables, log):
        action = self.get_action(name)
        return action(name, arglst, url, content, variables, log)


# Default actions

def noaction(name, arglst, url, content, variables, log):
    log.info("{} for url '{}'".format(name, url))
    log.debug("Arglst: {}".format(arglst))
    return {}

def email_notify(name, arglst, url, content, variables, log):
    log.debug("{} for {}".format(name, url))
    log.debug("Arglst: {}".format(arglst))
    return {}

def re_match(name, arglst, url, content, variables, log):
    log.debug("{} for {}".format(name, url))
    log.debug("Arglst: {}".format(arglst))
    return {}

def runscript(name, arglst, url, content, variables, log):
    log.debug("{} for {}".format(name, url))
    log.debug("Arglst: {}".format(arglst))
    return {}
