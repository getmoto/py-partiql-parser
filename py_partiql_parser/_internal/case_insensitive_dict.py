import sys

if sys.version_info[:2] >= (3, 8):
    from collections.abc import Mapping, MutableMapping
else:
    from collections import Mapping, MutableMapping
from collections import OrderedDict


class CaseInsensitiveDict(MutableMapping):
    # Taken from https://raw.githubusercontent.com/kennethreitz/requests/v2.25.1/requests/structures.py

    def __init__(self, data=None, **kwargs):
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    def get_original(self, key, get_default=None):
        if key.lower() not in self._store:
            return get_default
        original_key, original_value = self._store[key.lower()]
        return CaseInsensitiveDict({original_key: original_value})

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))
