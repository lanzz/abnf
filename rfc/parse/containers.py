from collections import OrderedDict


__all__ = [
    'Context',
    'Match',
]


class Context(OrderedDict):
    """Container for parse context.

    This is an ordered dictionary that also supports attribute access.
    """

    def __getattr__(self, name):
        """Convenience attribute accessor."""
        return self[name]

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


class Match(object):
    """Container for match of a rule."""

    def __init__(self, value, str_value=None, context=None, unparsed=None):
        """Initializer.

        :param value: value that can be captured (defaults to `match`)
        :param str_value: string value, if `value` is not string (see `Flatten`)
        :param context: dictionary of the parse context
        :param unparsed: remaining input string after the matching portion
        """
        self.value = value
        self.str_value = str_value if str_value is not None else str(value)
        self.context = Context() if context is None else context
        self.unparsed = unparsed

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '<Match {value!r}{unparsed}{context}>'.format(
            value=self.value,
            unparsed=', unparsed={unparsed!r}'.format(
                unparsed=self.unparsed,
            ) if self.unparsed else '',
            context=', context={context!r}'.format(
                context=self.context,
            ) if self.context else '',
        )
