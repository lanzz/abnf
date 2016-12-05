from collections import OrderedDict


__all__ = [
    'Context',
]


class Context(OrderedDict):
    """Container for parse context.

    This is an ordered dictionary that also supports attribute access.
    """

    def __getattr__(self, name):
        """Convenience attribute accessor."""
        return self[name]

    def __setattr__(self, name, value):
        """Convenience attribute accessor."""
        self[name] = value

    def __delattr__(self, name):
        """Convenience attribute accessor."""
        del self[name]

    def __repr__(self):
        """Render a representation similar to a dict.

        :returns: str
        """
        return '{{{items}}}'.format(
            items=', '.join(
                '{key!r}: {value!r}'.format(key=key, value=value)
                for key, value in self.items()
            ),
        )

    def clean(self):
        """Clean up internal sunder keys."""
        for key in list(self):
            if key.startswith('_'):
                del self[key]
        return self