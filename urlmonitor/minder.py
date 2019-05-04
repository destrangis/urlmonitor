import os
import sys
import pathlib
import shlex
import argparse
import importlib.util

import yaml

from .webchecker import WebChecker
from .nsdict import NSDict

URL_LIST_FILE = "urllist.yml"
PERSISTENCE_FILE = "./persistence.sqlite"
CONFIG_FILE = "./minderconfig.yml"

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


class Monitor:
    instance_counter = 0

    def __init__(self, obj, variables, log=None):
        Monitor.instance_counter += 1
        self.variables = variables

        if log is None:
            self.log = DummyLog()
        else:
            self.log = log

        self.name = obj.get("name", "ITEM_{:04d}".format(self.instance_counter))

        self.url = obj.get("url")
        if not self.url:
            self.log.warning("\tno URL found on '{}'".format(name))

        self.actions = []
        action_lst = obj.get("actions")
        if action_lst is None:
            self.log.warning("\t{} has no action list.".format(self.name))
        elif isinstance(action_lst, str):
            self.actions.append(shlex.split(action_lst))
        elif isinstance(action_lst, list):
            for act in action_lst:
                if not isinstance(act, dict):
                    self.log.error("Expected dict for action, got {}"
                                .format(act))
                    continue

                for name, val in act.items():
                    if isinstance(val, list):
                        actwords = [ name ] + val
                    else:
                        try:
                            actwords = [name] + shlex.split(val)
                        except Exception as xcp:
                            self.log.error("Bad action {}: {} - {}"
                                    .format(name, val, xcp))
                            continue
                    self.actions.append(actwords)

        else:
            self.log.error("Actions must be a string or a list of objects\n"
                      "Got: '{}'".format(action_lst))


    def run(self, webchecker, actionmgr):
        changed = True
        urldata = {}
        content = ""
        if self.url:
            self.log.info("Checking '{}'".format(self.url))
            changed = webchecker.check(self.url)
            urldata = webchecker.content.get(self.url, {})

        if not changed:
            self.log.info("No change in '{}'".format(self.url))
            return

        if urldata:
            content = urldata["new_content"]

        # make the results of checking available to the action
        self.variables.update(urldata)

        for act in self.actions:
            action_name = act[0]
            action_args = [ arg.format(**self.variables)
                                for arg in act[1:] ]
            self.log.debug("{} - Running action '{}'".format(self.url, action_name))
            self.log.debug("Args: {}".format(action_args))
            result_vars = actionmgr.run(action_name,
                                        action_args,
                                        self.url,
                                        content,
                                        self.variables,
                                        self.log)
            if result_vars:
                self.variables.update(result_vars)


class ActionManager:

    def __init__(self, config_file="", log=None):
        self.variables = NSDict(with_environment=True)
        if log == None:
            self.log = DummyLog()
        else:
            self.log = log
        self.action_dirs = []
        self.actionslst = []
        self.actions_configs = {}
        self.dict_vars = {}
        self.config_file = config_file
        self.config = None
        self.actions = {}

        self.configure(config_file)


    def load(self, config_file):
        if not config_file:
            self.config = {}
            return

        self.config_file = pathlib.Path(config_file)
        if self.config_file.is_file():
            with self.config_file.open() as fd:
                self.config = yaml.load(fd.read(), Loader=yaml.Loader)
        else:
            self.log.error("Not a valid configuration file: '{}'"
                            .format(config_file))
            self.config = {}


    def set_vars(self, vardict):
        """
        Store the contents of a set_vars section during configuration
        """
        self.dict_vars.update(vardict)


    def action_dir(self, actdir):
        if isinstance(actdir, str):
            self.action_dirs.append(actdir)
        elif isinstance(actdir, list):
            self.action_dirs += actdir
        else:
            self.log.error("action_dir can contain only string or list "
                            "of strings.\nFound: {}".format(actdir))

    def actions_config(self, actconfs):
        self.actions_configs.update(actconfs)


    def setup_actions(self, actlst):
        self.actionslst += actlst


    def configure(self, config_file):
        call_config = {
            "set_vars": self.set_vars,
            "action_dir": self.action_dir,
            "actions_config": self.actions_config,
            "actions": self.setup_actions,
        }

        self.load(config_file)
        for section_object in self.config:
            for section, value in section_object.items():
                f = call_config.get(section)
                if f:
                    f(value)
                else:
                    self.log.warning("Unrecognised section '{}'".format(section))

        self.install_actions()

        # set the variables by running the set_vars action
        self.run("set_vars", self.dict_vars, "", "")


    def load_actions_from_dir(self, directory):
        """
        Load all the actions in a given directory, by importing all
        the files with a .py extension.
        """
        for f in os.scandir(directory):
            if not f.name.endswith(".py"):
                continue

            if f.name.startswith("_") or f.name.startswith("test"):
                continue

            pf = pathlib.Path(f.path)
            modname = pf.stem
            self.log.debug("Installing action '{}'".format(modname))

            spec = importlib.util.spec_from_file_location(modname, f.path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.actions[modname] = module.action_object


    def install_action_object(self, act):
        """
        Install one action given by act, a mapping with at least
        the entries "name" - name of the action,
        and "module" - the Python file to import the action from.

        The module must define and export a callable called "action_object"
        The rest of the entries in act are action configuration entries.
        At a later stage, the action_object.initialise() method is called
        (if it exists) with the configuration dictionary.
        """
        try:
            action_name = act.pop("name")
        except KeyError:
            self.log.error("Ignoring action with no name: {}"
                            .format(act))
            return

        try:
            action_path = pathlib.Path(act.pop("module"))
        except KeyError:
            self.log.error("Ignoring action '{}' with no module: {}"
                            .format(action_name, act))
            return

        module_dir = action_path.parent
        modname = action_path.stem

        spec = importlib.util.spec_from_file_location(modname, str(action_path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.actions[action_name] = module.action_object
        self.actions_configs[action_name] = act


    def install_actions(self):
        # install default actions
        self.actions["set_vars"] = action_set_global_vars
        self.actions["list_vars"] = action_list_vars
        self.actions["do_nothing"] = noaction

        # install predefined actions
        this_file = pathlib.Path(__file__)
        predefined_actions_dir = this_file.parent / "actions"
        self.log.debug("Loading predefined actions from '{}'"
                        .format(predefined_actions_dir))
        self.load_actions_from_dir(predefined_actions_dir)

        # install actions from action_dir sections
        for actdir in self.action_dirs:
            self.log.debug("Loading actions from: {}".format(actdir))
            self.load_actions_from_dir(actdir)

        # install actions from action sections
        for act_obj in self.actionslst:
            self.install_action_object(act_obj)

        # configure the actions
        fails = []
        for actname, action_object in self.actions.items():
            self.log.debug("Configuring action '{}'".format(actname))

            conf_object = self.actions_configs.get(actname, {})
            if hasattr(action_object, "initialise"):
                try:
                    action_object.initialise(conf_object)
                except Exception as xcp:
                    self.log.error("Could not initialise action '{}'\n{}"
                                    .format(actname, xcp))
                    fails.append(actname)

        for actname in fails:
            self.actions[actname] = noaction


    def run(self, name, arglst, url, content, variables=None, log=None):
        """
        Run an action
        """
        if variables is None:
            variables = self.variables
        if log is None:
            log = self.log

        action = self.actions.get(name, noaction)
        return action(name, arglst, url, content, variables, log)


    def process(self, minderlst, webchecker):
        """
        For each object in minderlst, check the url and run the actions
        """
        for obj in minderlst:
            self.variables.push()   # create a new scope
            Monitor(obj, self.variables, log=self.log).run(webchecker, self)
            self.variables.pop()   # lose the variables created by the action


# default actions
def action_set_global_vars(name, arglst, url, content, variables, log):
    for key, val in arglst:
        log.debug("{}: setting '{}' to {}".format(name, key, val))
        variables.set_global(key, val)

def action_list_vars(name, arglst, url, content, variables, log):
    log.debug("{}:".format(name))
    for var, value in variables.items():
        log.debug("\t{} = '{}'".format(var, value))

def noaction(name, arglst, url, content, variables, log):
    log.info("NO ACTION {} for url '{}'".format(name, url))
    log.debug("Arglst: {}".format(arglst))
    return {}


def parse_cli_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--config", "-c", metavar="FILE", default=None,
            help="Configuration file.")
    p.add_argument("--urlcheck", "-u", metavar="FILE", default=URL_LIST_FILE,
            help="Url check specification. Default: " + URL_LIST_FILE)
    p.add_argument("--persist-file", "-p", metavar="FILE", default=PERSISTENCE_FILE,
            help="Persistence file to store URL status. Default " +
                    PERSISTENCE_FILE)
    return p.parse_args(argv)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    opts = parse_cli_args(argv)

    log = DummyLog()

    urls = pathlib.Path(opts.urlcheck)
    if urls.is_file():
        with urls.open() as fd:
            to_check = yaml.load(fd.read(), Loader=yaml.Loader)
    else:
        log.error("Cannot find '{}'".format(opts.urlcheck))

    actionmgr = ActionManager(opts.config, log)
    webcheck = WebChecker(opts.persist_file)

    actionmgr.process(to_check, webcheck)


if __name__ == "__main__":
    main()
