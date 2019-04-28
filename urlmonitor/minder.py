import sys
import pathlib
import shlex

import yaml


from urlmanager import UrlManager
from actionmanager import ActionManager

URL_LIST_FILE = "urllist.yml"

class DummyLog:

    def __init__(self, outfile=sys.stderr):
        if isinstance(outfile, str):
            self.fd = open(outfile, "a")
        else:
            self.fd = outfile

    def log(self, severity, msg):
        print("{}: {}".format(severity, msg), file=self.fd)

    def info(self, msg):
        self.log("INFO", msg)

    def warning(self, msg):
        self.log("WARNING", msg)

    def error(self, msg):
        self.log("ERROR", msg)

    def debug(self, msg):
        self.log("DEBUG", msg)

    def critical(self, msg):
        self.log("CRITICAL", msg)




class UrlItem:
    instance_counter = 0

    def __init__(self, obj, default_vars=None, log=None):
        UrlItem.instance_counter += 1

        self.variables = {}
        if default_vars is not None:
            for var, value in default_vars.items():
                self.variables[var] = value

        if log is None:
            self.log = DummyLog()
        else:
            self.log = log

        self.name = obj.get("name", "ITEM_{:04d}".format(self.instance_counter))

        self.url = obj.get("url")
        if not self.url:
            log.warning("\tno URL found on '{}'".format(name))

        self.actions = []
        action_lst = obj.get("actions")
        if action_lst is None:
            log.warning("\t{} has no action list.".format(self.name))
        elif isinstance(action_lst, str):
            self.actions.append(shlex.split(action_lst))
        elif isinstance(action_lst, list):
            for act in action_lst:
                if isinstance(act, dict):
                    for name, val in act.items():
                        if isinstance(val, list):
                            actwords = [ name ] + val
                        else:
                            try:
                                actwords = [name] + shlex.split(val)
                            except Exception as xcp:
                                log.error("Bad action {}: {} - {}"
                                        .format(name, val, xcp))
                                continue
                        self.actions.append(actwords)
                else:
                    log.error("Expected dict for action, got {}"
                                .format(act))
        else:
            log.error("Actions must be a string or a list of objects\n"
                      "Got: '{}'".format(action_lst))


    def run(self, urlmanager, actionmgr):
        changed = True
        content = ""
        if self.url:
            changed = urlmanager.check(self.url)
            content = urlmanager.content.get(self.url, "")

        if not changed:
            self.log.info("No change in '{}'".format(self.url))
            return

        for act in self.actions:
            action_name = act[0]
            action_args = [ arg.format(**self.variables)
                                for arg in act[1:] ]
            result_vars = actionmgr.run(action_name,
                                        action_args,
                                        self.url,
                                        content,
                                        self.variables,
                                        self.log)
            self.variables.update(result_vars)



def remind(minderlst, urlmanager, actionmanager, log=None):
    """
    For each object in minderlst, check the url and run the actions
    """
    if log is None:
        log = DummyLog(sys.stderr)

    for obj in minderlst:
        UrlItem(obj, log=log).run(urlmanager, actionmanager)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    log = DummyLog()
    urls = pathlib.Path(URL_LIST_FILE)
    if urls.is_file():
        with urls.open() as fd:
            to_check = yaml.load(fd.read(), Loader=yaml.Loader)
    else:
        log.error("Cannot find '{}'".format(URL_LIST_FILE))

    urlmgr = UrlManager(".")
    actmgr = ActionManager()
    remind(to_check, urlmgr, actmgr, log)


if __name__ == "__main__":
    main(sys.argv)
