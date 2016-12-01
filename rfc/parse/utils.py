from functools import wraps


__all__ = ['CharRange']


def _relay_op(method):
    """Relay a method to the underlying chars set.

    Binary operations will attempt to cast their argument to `CharRange`
    if it is a string or an integer, allowing for ``CharRange(...) | 'abc'``
    usage for convenience.

    If return value of the operation is a set, it will be cast to `CharRange`
    (e.g. a & b, a | b), otherwise will be returned as-is (len(cr), iter(cr), etc).

    :param method: name of the method to relay to
    :returns: function
    """
    method = getattr(set, method)
    @wraps(method)
    def op(self, other=None):
        if other is None:
            return method(self.chars)
        if isinstance(other, (str, int)):
            other = type(self)(other)
        elif not isinstance(other, CharRange):
            return NotImplemented
        value = method(self.chars, other.chars)
        if isinstance(value, set):
            value = type(self)(value)
        return value
    return op


class CharRange(object):
    """Range of characters."""

    def __init__(self, start, end=None):
        """Initializer.

        :param start: start of range or entire string of characters to match
        :param end: end of range or None
        """
        if end is None:
            chars = chr(start) if isinstance(start, int) else start
        else:
            if not isinstance(start, int):
                start = ord(start)
            if not isinstance(end, int):
                end = ord(end)
            chars = (chr(c) for c in range(start, end + 1))
        self.chars = set(chars)

    def __str__(self):
        """Stringify to the list of matched characters."""
        return ''.join(sorted(self.chars))

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '<CharRange {chars!r}>'.format(chars=str(self))

    # all set operations are relayed to the underlying `chars` set
    __iter__ = _relay_op('__iter__')
    __len__ = _relay_op('__len__')
    __contains__ = _relay_op('__contains__')
    __le__ = _relay_op('__le__')
    __lt__ = _relay_op('__lt__')
    __ge__ = _relay_op('__ge__')
    __gt__ = _relay_op('__gt__')
    __or__ = _relay_op('__or__')
    __and__ = _relay_op('__and__')
    __sub__ = _relay_op('__sub__')
    __xor__ = _relay_op('__xor__')

    def copy(self):
        """Return a copy."""
        return type(self)(self.chars)
