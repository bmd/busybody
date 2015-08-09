
class SeekableDict(dict):
    """
    A dict seekable to arbitrary depth without committing to the existance of a parent key. Seekable in all kinds
    of awesome and crazy ways.

    d = SeekableDict(a_normal_dict)
    deep_value = d['k1', 'k2', 'k3', 'sought_key']

    keys_to_seek = ['k1', 'k2', 'k3', 'sought_key']
    deep_value = d[*keys_to_seek]

    Nested dictionary of arbitrary depth with autovivification.
    Allows data access via extended slice notation.

    http://stackoverflow.com/questions/15077973/how-can-i-access-a-deeply-nested-dictionary-using-tuples
    """
    def __getitem__(self, keys, default=None):
        if not isinstance(keys, basestring):
            try:
                node = self
                for key in keys:
                    node = dict.__getitem__(node, key)
                return node
            except TypeError:
                return default
            except KeyError:
                return default
        try:
            return dict.__getitem__(self, keys)
        except KeyError:
            return default

    def __setitem__(self, keys, value):
        if not isinstance(keys, basestring):
            try:
                node = self
                for key in keys[:-1]:
                    try:
                        node = dict.__getitem__(node, key)
                    except KeyError:
                        node[key] = type(self)()
                        node = node[key]
                return dict.__setitem__(node, keys[-1], value)
            except TypeError:
                pass

        dict.__setitem__(self, keys, value)
