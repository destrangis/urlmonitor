import os


class NSDict:
    """
    Dictionary with scopes.

    >>> dd = nsdict.NSDict(with_environment=False)
    >>> dd["a"] = 1; dd["b"] = 2; dd["c"] = 3; dd["d"] = 4
    >>> dd.push({"a": 11, "d": 44, "J": 55})
    NSDict(with_environment=False).push({'a': 1, 'b': 2, 'c': 3, 'd': 4, }).push({'a': 11, 'd': 44, 'J': 55, })
    >>> str(dd)
    "NSDict({'a': 11, 'b': 2, 'c': 3, 'd': 44, 'J': 55, })"
    >>> str(dd.pop())
    "NSDict({'a': 1, 'b': 2, 'c': 3, 'd': 4, })"
    >>> dd
    NSDict(with_environment=False).push({'a': 1, 'b': 2, 'c': 3, 'd': 4, })


    """

    def __init__(self, mapping=None, with_environment=True):
        self.mappings = []
        if mapping is not None:
            self.mappings = [mapping]
        self.with_environment = with_environment

    def push(self, mapping=None):
        if mapping is None:
            mapping = {}

        self.mappings.append(mapping)
        return self

    def pop(self):
        self.mappings.pop()
        return self

    def set_global(self, key, val):
        if not self.mappings:
            self.mappings.append({key: val})
        else:
            self.mappings[0][key] = val

    def __getitem__(self, key):
        for mapping in self.mappings[-1::-1]:
            if key in mapping:
                return mapping[key]
        if self.with_environment:
            return os.environ[key]  # KeyError if key is not in env
        return self.__missing__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, val):
        if not self.mappings:
            self.mappings.append({key: val})
        else:
            self.mappings[-1][key] = val

    def __missing__(self, k):
        raise KeyError

    def _traverse(self, access=None):
        keys_found = set()
        for mapping in self.mappings:
            for key in mapping.keys():
                if not key in keys_found:
                    keys_found.add(key)
                    yield access(key)

    def keys(self):
        yield from self._traverse(lambda k: k)

    def values(self):
        yield from self._traverse(lambda k: self[k])

    def items(self):
        yield from self._traverse(lambda k: (k, self[k]))

    def update(self, mapping):
        for key, val in mapping.items():
            self[key] = val

    def __str__(self):
        s = self.__class__.__name__ + "({"
        for k, v in self.items():
            s += repr(k) + ": " + repr(v) + ", "
        s += "})"
        return s

    def __repr__(self):
        s = self.__class__.__name__ + "({})".format(
            "with_environment=False" if not self.with_environment else ""
        )
        for mapping in self.mappings:
            s += ".push({"
            for k, v in mapping.items():
                s += repr(k) + ": " + repr(v) + ", "
            s += "})"
        return s

    def __len__(self):
        ln = 0
        for k in self.keys():
            ln += 1
        return ln

    def __contains__(self, k):
        try:
            x = self[k]
        except KeyError:
            return False
        return True

    def __iter__(self):
        class NSDict_iterator:
            def __init__(self_local):
                self_local.gen = self.keys()

            def __next__(self_local):
                return next(self_local.gen)

        return NSDict_iterator()
