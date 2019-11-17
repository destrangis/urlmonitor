class ActionError(Exception):
    pass


class Action:

    check_cfg_vars = []
    default_vars = {}

    def initialise(self, vardict):
        for var, value in vardict.items():
            setattr(self, var, value)

        missing = []
        for vname in self.check_cfg_vars:
            if not getattr(self, vname, None):
                defval = self.default_vars.get(vname)
                if defval is not None:
                    setattr(self, vname, defval)
                else:
                    missing.append(vname)

        if missing:
            raise ActionError(
                "Action {} - Missing config vars: {}".format(
                    __name__, ", ".join(missing)
                )
            )

    initialize = initialise

    def __call__(self, name, arglst, url, content, variables, log):
        raise ActionError(
            "__call__() method in '{}' must be overridden".format(
                self.__class__.__name__
            )
        )
