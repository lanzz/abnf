from .containers import Context
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

    def parse(self, s, context):
        """Relay the parse to the underlying rule.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        return self.rule.parse(s, context=context)


class FullMatch(RuleWrapper):
    """Match the full string, leaving no remainder."""

    def __repr__(self):
        """Render representation."""
        return '{rule!r} <END>'.format(rule=self.rule)

    def parse(self, s, context):
        """Assert there's no unparsed leftover after match.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        context = super(FullMatch, self).parse(s, context=context)
        if context._unparsed:
            raise NoMatchError(rule=self, unparsed=context._unparsed)
        return context


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

    def parse(self, s, context):
        """Return a default match in case rule does not match.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        try:
            context = super(Optional, self).parse(s, context=context.copy())
        except NoMatchError:
            context.update(
                _match='',
                _unparsed=s,
            )
        return context


class Capture(RuleWrapper):
    """Capture rule value in the parse context."""

    def __init__(self, rule, name, transform=None, raw=None):
        """Initializer.

        :param rule: rule to wrap
        :param name: context name for the captured value
        :param raw: capture the raw value instead of the capturable value
        """
        super(Capture, self).__init__(rule)
        assert not name.startswith('_'), 'Capture name cannot start with underscore'
        self.name = name
        self.transform = transform
        self.raw = False if raw is None else raw

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '<{name!r} = {rule!r}>'.format(
            name=self.name,
            rule=self.rule,
        )

    def parse(self, s, context):
        """Store the match as a named value in the context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        context = super(Capture, self).parse(s, context=context)
        if self.raw or ('_capturable' not in context):
            value = context._match
        else:
            value = context._capturable
        if self.transform:
            value = self.transform(value)
        context.update({
            self.name: value,
        })
        return context

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
        self.fn = fn if callable(fn) else lambda m: fn

    def parse(self, s, context):
        """Transform the match.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        context = super(Transform, self).parse(s, context=context)
        context._match = self.fn(context._match)
        return context


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

    def parse(self, s, context):
        """Fail a successful match if the condition fails.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        context = super(Assert, self).parse(s, context=context)
        if not self.condition(context):
            raise NoMatchError(rule=self, unparsed=s)
        return context


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

    def parse(self, s, context):
        """Parse a string.

        The capturable value will be a list of the contexts of each repeated match.
        If you need to capture the textual match, you can specify ``Capture(..., flat=True)``.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
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
                    iter_context = self.rule.parse(remainder, context=iter_context)
                else:
                    # subsequent matches include the delimiter (if any)
                    iter_context = delim_rule.parse(remainder, context=iter_context)
            except NoMatchError:
                break
            if remainder == iter_context._unparsed:
                # a zero-length match will keep matching forever
                raise RuntimeError('Zero-length match in Repeat rule: {rule!r}'.format(
                    rule=delim_rule if matches else self.rule,
                ))
            # discard the parent context, it was only there for the benefit of the child rule
            del iter_context['parent']
            matches.append(iter_context)
            remainder = iter_context._unparsed
            if not remainder:
                break
        if len(matches) < self.min:
            raise NoMatchError(rule=self, unparsed=s)
        context.update(
            _match=''.join(match._match for match in matches),
            _capturable=[match.clean() for match in matches],
            _unparsed=remainder,
        )
        return context

    def __getitem__(self, item):
        """Item accessor.

        Avoid rewrapping Repeat instances in another Repeat instances,
        return a copy with updated limits instead.
        """
        overrides = None
        if isinstance(item, int):
            overrides = dict(min=item, max=item)
        elif isinstance(item, slice) and not isinstance(item.start, str):
            overrides = dict(min=item.start or 0, max=item.stop)
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

    def parse(self, s, context):
        """Transform the value of the match.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        context = super(Mapping, self).parse(s, context=context)
        if isinstance(context.get('_capturable'), list):
            context._capturable = Context(
                (kvpair[self.key_name], kvpair[self.value_name])
                for kvpair in match._capturable
            )
        return context


# shorthand names

N = Capture     # (N)ame
NC = CaseFold   # (N)o(C)ase
Ign = Ignore
Map = Mapping
Opt = Optional
Rep = Repeat
XF = Transform