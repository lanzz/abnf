from .containers import Context, Match
from .rules import ensure_rule, Literal, NoMatchError, Rule


__all__ = [
    'Assert',
    'Capture',
    'CaseFold',
    'Ignore',
    'Mapping',
    'Optional',
    'Repeat',
    'Transform',
    'N', 'NC', 'Ign', 'Map', 'Opt', 'Rep', 'XF',
]


class RuleWrapper(Rule):
    """Rule that wraps another Rule."""

    def __init__(self, rule):
        """Initializer.

        :param rule: rule to wrap
        """
        super(RuleWrapper, self).__init__()
        self.rule = ensure_rule(rule)

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return repr(self.rule)

    def parse(self, s, context=None):
        """Wrap the underlying rule's parse method.

        :param s: string to parse
        :returns: the result of the underlying rule's parse
        """
        return self.rule.parse(s, context=context)


class FullMatch(RuleWrapper):
    """Match the full string, leaving no remainder."""

    def __repr__(self):
        """Render representation."""
        return '{rule!r} <END>'.format(rule=self.rule)

    def parse(self, s, context=None):
        match = super(FullMatch, self).parse(s, context=context)
        if match.unparsed:
            raise NoMatchError(rule=self, unparsed=match.unparsed)
        return match


class Optional(RuleWrapper):
    """Optionally match a rule."""

    def __init__(self, rule, default=None):
        """Initializer.

        :param rule: rule to wrap
        :param default: value to return in case of no match (defaults to '')
        """
        super(Optional, self).__init__(rule)
        self.default = default if default is not None else ''

    def __repr__(self):
        """Render representation."""
        return '[ {rule!r} ]'.format(rule=self.rule)

    def __invert__(self):
        """No need to wrap into another `Optional`, return self.

        :returns: self
        """
        return self

    def parse(self, s, context=None):
        """Return an empty match in case rule does not match.

        :param s: string to parse
        :returns: `Match`
        """
        try:
            match = super(Optional, self).parse(s, context=context)
        except NoMatchError:
            match = Match(value=self.default, unparsed=s)
        return match


class Capture(RuleWrapper):
    """Capture rule value in the parse context."""

    def __init__(self, rule, name, raw=None):
        """Initializer.

        :param rule: rule to wrap
        :param name: context name for the captured value
        :param raw: capture the raw value instead of the capturable value
        """
        super(Capture, self).__init__(rule)
        self.name = name
        self.raw = False if raw is None else raw

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '<{name!r} = {rule!r}>'.format(
            name=self.name,
            rule=self.rule,
        )

    def parse(self, s, context=None):
        """Return an empty match in case rule does not match.

        :param s: string to parse
        :returns: `Match` or None
        """
        assert context is not None, 'Cannot capture without a context'
        match = super(Capture, self).parse(s, context=context)
        value = match.value if self.raw or (match.capturable is None) else match.capturable
        context.update({
            self.name: value,
        })
        return match

    def __pos__(self):
        """Capture the raw value instead of the capturable value.

        Rep(L('foo')['in'])['out'] => {'out': [{'in': 'foo'}, {'in': 'foo'}]}
        +Rep(L('foo')['in'])['out'] => {'out': 'foofoo'}

        `Repeat` rules are usually captured as a list of each matching repetition's context.
        This is not always desirable; flattening will capture the string value instead.

        :returns: `Capture`
        """
        return Capture(self.rule, self.name, raw=True)


class Transform(RuleWrapper):
    """Transform the value of a match."""

    def __init__(self, rule, fn):
        """Initializer.

        :param rule: rule to wrap
        :param fn: function to call on the match value
        """
        super(Transform, self).__init__(rule)
        self.fn = fn

    def parse(self, s, context=None):
        """Transform the match value.

        :param s: string to parse
        :returns: `Match` or None
        """
        match = super(Transform, self).parse(s, context=context)
        match.value = self.fn(match.value)
        return match


def Ignore(rule):
    """Ignore the value of the matched rule.

    :param rule: rule to wrap
    :returns: `Transform`
    """
    return Transform(rule, lambda v: '')


def CaseFold(rule):
    """Casefold the value of a match.

    :param rule: rule to wrap
    :returns: `Transform`
    """
    return Transform(rule, lambda v: v.casefold())


class Assert(RuleWrapper):
    """Assert an additional condition on a rule match."""

    def __init__(self, rule, condition, *args, **kwargs):
        """Initializer.

        :param rule: rule to wrap
        :param condition: condition function to satisfy
        """
        super(Assert, self).__init__(rule, *args, **kwargs)
        self.condition = condition

    def parse(self, s, context=None):
        """Fail a successful match if the condition fails.

        :param s: string to parse
        :returns: `Match` or None
        """
        match = super(Assert, self).parse(s, context=context)
        if not self.condition(match):
            raise NoMatchError(rule=self, unparsed=s)
        return match


class Repeat(RuleWrapper):
    """Repeatly match a rule in sequence."""

    def __init__(self, rule, delimiter=None, min=0, max=None):
        """Initializer.

        :param rule: rule to wrap
        :param delimiter: additional rule to match between repetitions of `rule`
        :param min: minimum number of matches
        :param max: maximum number of matches
        """
        super(Repeat, self).__init__(rule)
        self.delimiter = ensure_rule(delimiter)
        self.min = min
        self.max = max

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '{len}({rule!r}{delimiter})'.format(
            len='{min}*{max}'.format(
                min='' if not self.min else self.min,
                max='' if not self.max else self.max,
            ) if (self.min, self.max) != (0, None) else '*',
            rule=self.rule,
            delimiter=' [delim={delimiter!r}]'.format(
                delimiter=self.delimiter,
            ) if self.delimiter is not None else '',
        )

    def parse(self, s, context=None):
        """Collect all matches and wrap them in a overall `Match`.

        The capturable value of the returned `Match` will be a list
        of the contexts of each repeated match. If you need to capture
        the textual match, you can specify ``Capture(..., flat=True)``.

        :param s: string to parse
        :returns: `Match` or None
        """
        matches = []
        remainder = s
        if self.delimiter is not None:
            delim_rule = self.delimiter + self.rule
        else:
            delim_rule = self.rule
        while True:
            if (self.max is not None) and (len(matches) >= self.max):
                break
            # instantiate a fresh context for the iteration
            # and make the parent context available as a key
            iter_context = Context(parent=context)
            try:
                if not matches:
                    # first match, no delimiter
                    match = self.rule.parse(remainder, context=iter_context)
                else:
                    # subsequent matches include the delimiter (if any)
                    match = delim_rule.parse(remainder, context=iter_context)
            except NoMatchError:
                break
            if remainder == match.unparsed:
                # a zero-length match will keep matching forever
                rule = self.rule
                if self.delimiter is not None:
                    rule = self.delimiter + self.rule
                raise RuntimeError('Zero-length match in Repeat rule: {rule!r}'.format(
                    rule=(self.delimiter + self.rule) if self.delimiter is not None else self.rule,
                ))
            # discard the parent context, it was only there for the benefit of the child rule
            del iter_context['parent']
            matches.append((match, iter_context))
            remainder = match.unparsed
            if not remainder:
                break
        if len(matches) < self.min:
            raise NoMatchError(rule=self, unparsed=s)
        capturable = [context for _, context in matches]
        value = ''.join(match.value for match, _ in matches)
        match = Match(value=value, capturable=capturable, unparsed=remainder)
        return match

    def __getitem__(self, item):
        """Item accessor.

        Avoid rewrapping Repeat instances in another Repeat instances,
        return a copy with updated limits instead.
        """
        if isinstance(item, int):
            overrides = dict(min=item, max=item)
        elif isinstance(item, slice):
            overrides = dict(min=item.start or 0, max=item.stop)
        else:
            overrides = None
        if overrides:
            return Repeat(self.rule, delimiter=self.delimiter, **overrides)
        else:
            # delegate unhandled cases to super
            return super(Repeat, self).__getitem__(item)


class Mapping(Repeat):
    """Transform a capturable list of kvpairs into a mapping."""

    def __init__(self, *args, key_name=None, value_name=None, **kwargs):
        """Initializer.

        :param *args: arguments to pass through to super
        :param *kwargs: keyword arguments to pass through to super
        :param key_name: name of context value to use for mapping keys (defaults to "key")
        :param value_name: name of context value to use for mapping values (defaults to "value")
        """
        super(Mapping, self).__init__(*args, **kwargs)
        self.key_name = key_name or 'key'
        self.value_name = value_name or 'value'

    def parse(self, s, context=None):
        """Transform the value of the match.

        :param s: string to parse
        :returns: `Match` or None
        """
        match = super(Mapping, self).parse(s, context=context)
        match.capturable = Context(
            (kvpair[self.key_name], kvpair[self.value_name])
            for kvpair in match.capturable
        )
        return match


# shorthand names

N = Capture     # (N)ame
NC = CaseFold   # (N)o(C)ase
Ign = Ignore
Map = Mapping
Opt = Optional
Rep = Repeat
XF = Transform