import re

from .containers import Context


__all__ = [
    'NoMatchError',
    'Alternatives',
    'Chars',
    'Literal',
    'LiteralCS',
    'Reference',
    'RegExp',
    'Sequence',
    'Alt', 'Ch', 'L', 'LC', 'Ref', 'Rx', 'Seq',
]


def ensure_rule(value):
    """Ensure value is a `Rule`.

    If the value is not a `Rule`, it will be stringified and wrapped into a `Literal` instance.

    :param value: value to wrap
    :returns: `Rule`
    """
    if not isinstance(value, (Rule, type(None))):
        value = Literal(str(value))
    return value


class NoMatchError(ValueError):
    """Indicates a failed parse."""

    def __init__(self, *args, rule=None, unparsed=None):
        """Initializer.

        :param args: arguments to pass through to super
        :param rule: rule that failed to match
        :param unparsed: string that was being parsed
        """
        super(NoMatchError, self).__init__(*args)
        self.rule = rule
        self.unparsed = unparsed


class Rule(object):
    """Base class for all parser rules."""

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        # by default, do not match anything
        raise NoMatchError(rule=self, unparsed=s)

    def __call__(self, s, partial=False):
        """Parse a string and return its values.

        :param s: string to parse
        :param partial: boolean indicating whether to accept a partial match at start of ``s``
        """
        from .wrappers import FullMatch
        context = Context()
        context = FullMatch(self).parse(s, context)
        return context.clean()

    def __getitem__(self, item):
        """Item accessor.

        rule['foo']     => capture the rule as "foo"
        rule['foo':fn]  => filter the value of the rule through fn and capture it as "foo"
        rule[:1]        => optional rule
        rule[5]         => repeat the rule exactly 5 times
        rule[5:]        => repeat the rule at least 5 times
        rule[:5]        => repeat the rule up to 5 times
        rule[1:5]       => repeat the rule 1 to 5 times
        rule[:]         => repeat the rule any number of times
        rule[1:5:',']   => repeat the rule 1 to 5 times, delimited by ','

        :param item: item selector
        :returns: `Capture`, `Optional` or `Repeat` rule
        :raises: `KeyError` if `item` is of a wrong type
        """
        cap = None
        reps = None
        if isinstance(item, str):
            # capture
            cap = dict(
                name=item,
            )
        if isinstance(item, int):
            # exact repetitions
            reps = dict(min=item, max=item)
        elif isinstance(item, slice):
            if isinstance(item.start, str):
                # capture with transform
                cap = dict(
                    name=item.start,
                    transform=item.stop,
                )
            else:
                # range of repetitions
                reps = dict(
                    min=item.start or 0,
                    max=item.stop,
                    delimiter=item.step
                )
        if cap:
            # capture
            from .wrappers import Capture
            return Capture(self, **cap)
        if reps:
            # repeat
            if (reps['min'], reps['max']) == (0, 1):
                # 0 to 1 reps => Optional
                from .wrappers import Optional
                return Optional(self)
            else:
                # range of repetitions
                from .wrappers import Repeat
                return Repeat(self, **reps)
        raise KeyError(item)

    def __invert__(self):
        """Make rule optional.

        :returns: `Optional`
        """
        from .wrappers import Optional
        return Optional(self)

    def __add__(self, other):
        """Combine self and other into a `Sequence`.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(self, other)

    def __radd__(self, other):
        """Combine other and self into a `Sequence`.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(other, self)

    def __mul__(self, other):
        """Combine self and other into a `Sequence`.

        Whitespace between rules will be ignored.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(self, WS(), other)

    def __rmul__(self, other):
        """Combine other and self into a `Sequence`.

        Whitespace between rules will be ignored.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(other, WS(), self)

    def __or__(self, other):
        """Combine self and other into an `Alternatives`.

        :returns: `Alternatives`
        """
        other = ensure_rule(other)
        return Alternatives(self, other)

    def __ror__(self, other):
        """Combine other and self into an `Alternatives`.

        :returns: `Alternatives`
        """
        other = ensure_rule(other)
        return Alternatives(other, self)


class WS(Rule):
    """Strip non-significant whitespace."""

    def __repr__(self):
        """Render representation."""
        return '[ <WS> ]'

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        unparsed = s.lstrip()
        context.update(
            _match='',
            _unparsed=unparsed,
        )
        return context


class Literal(Rule):
    """Rule matching one of a set of literal strings.

    Case-insensitive by default; pass casefold=False or use the
    LiteralCS alternate constructor for case-sensitive match.
    """

    def __init__(self, *literals, casefold=None):
        """Initializer.

        :param literals: literal strings to match
        :param casefold: boolean indicating if matching should be case-folded
        """
        super(Literal, self).__init__()
        self.casefold = True if casefold is None else casefold
        if self.casefold:
            literals = [literal.casefold() for literal in literals]
        self.literals = literals
        assert len(self.literals) > 0, 'Need at least one literal to match'

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        if len(self.literals) == 1:
            return repr(self.literals[0])
        return '({literals})'.format(
            literals=' | '.join(map(repr, self.literals)),
        )

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        cs = s.casefold() if self.casefold else s
        for literal in self.literals:
            if not cs.startswith(literal):
                continue
            match_len = len(literal)
            match = cs[:match_len]
            context.update(
                _match=match,
                _unparsed=s[match_len:],
            )
            return context
        raise NoMatchError(rule=self, unparsed=s)


def LiteralCS(*literals):
    """Rule matching a case-sensitive literal.

    :param literals: literal strings to match
    :returns: `Literal`
    """
    return Literal(*literals, casefold=False)


class RegExp(Rule):
    """Rule matching a regular expression at start of input."""

    def __init__(self, regexp, flags=None):
        """Initializer.

        :param regexp: regular expression to match
        :param flags: regular expression flags
        """
        super(RegExp, self).__init__()
        if isinstance(regexp, str):
            regexp = re.compile(regexp, flags or 0)
        self.regexp = regexp

    def __repr__(self):
        """Render representation."""
        return '/{rx}/'.format(
            rx=self.regexp.pattern.replace('\\', '\\\\').replace('/', '\\/'),
        )

    def parse(self, s, context):
        """Parse a string into the parse context.

        Named groups will be captured as context keys.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        m = self.regexp.match(s)
        if not m:
            raise NoMatchError(rule=self, unparsed=s)
        groupdict = m.groupdict()
        assert not any(key.startswith('_') for key in groupdict), 'Capture name cannot start with underscore'
        match = m.group(0)
        context.update(
            _match=match,
            _unparsed=s[len(match):],
            **m.groupdict()
        )
        return context


class Chars(Rule):
    """Rule matching a run of allowed characters."""

    def __init__(self, chars=None, exclude=None, min=1, max=1):
        """Initializer.

        :param chars: characters to match
        :param exclude: characters to exclude from match
        :param min: minimum number of matching characters
        :param max: maximum number of matching characters
        """
        super(Chars, self).__init__()
        self.chars = None if chars is None else set(chars)
        self.exclude = None if exclude is None else set(exclude)
        self.min = min
        self.max = max
        if self.exclude is None:
            self._predicate = lambda c: c in self.chars
        elif self.chars is None:
            self._predicate = lambda c: c not in self.exclude
        else:
            self._predicate = lambda c: (c in self.chars) and (c not in self.exclude)

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '{len}<{chars}{exclude}>'.format(
            len='{min}*{max}'.format(
                min='' if not self.min else self.min,
                max='' if not self.max else self.max,
            ) if (self.min, self.max) != (0, None) else '*',
            chars='{chars!r}'.format(
                chars=''.join(sorted(self.chars)),
            ) if self.chars is not None else 'any',
            exclude=' except {exclude!r}'.format(
                exclude=self.exclude,
            ) if self.exclude is not None else '',
        )

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        if self.chars is self.exclude is None:
            # match anything
            match_len = len(s)
        elif len(s):
            for match_len, c in enumerate(s):
                if not self._predicate(c):
                    break
            else:
                match_len += 1
        else:
            match_len = 0
        if self.max is not None:
            match_len = min(match_len, self.max)
        if match_len < self.min:
            # not enough matching characters
            raise NoMatchError(rule=self, unparsed=s)
        context.update(
            _match=s[:match_len],
            _unparsed=s[match_len:],
        )
        return context

    def __getitem__(self, item):
        """Item accessor.

        Avoid wrapping Chars instances in Repeat instances,
        return a copy with updated limits instead.

        :param item: item selector
        :returns: `Chars` or super
        """
        overrides = None
        if isinstance(item, int):
            overrides = dict(min=item, max=item)
        elif isinstance(item, slice) and not isinstance(item.start, str) and item.step is None:
            # only return a copy if slice start is not str (which would be a Capture rule)
            # and has no step (which would be a delimiter for a Repeat rule)
            overrides = dict(min=item.start or 0, max=item.stop)
        if overrides:
            return Chars(self.chars, self.exclude, **overrides)
        else:
            return super(Chars, self).__getitem__(item)


class Sequence(Rule):
    """Rule matching a sequence of rules in order."""

    def __init__(self, *rules):
        """Initializer.

        :param rules: rules to match
        """
        super(Sequence, self).__init__()
        self.rules = tuple(ensure_rule(rule) for rule in rules)

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '({rules})'.format(
            rules=' '.join(map(repr, self.rules)),
        )

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        matches = []
        context._unparsed = s
        for rule in self.rules:
            iter_context = rule.parse(context._unparsed, context=context)
            if iter_context is not context:
                context.update(iter_context)
            # discard any received capturable value
            if '_capturable' in context:
                del context['_capturable']
            matches.append(context._match)
        context.update(
            _match=''.join(matches),
        )
        return context

    def __add__(self, other):
        """Append another rule to the sequence.

        :param other: rule to append
        :returns: `Sequence`
        """
        other = ensure_rule(other)
        if isinstance(other, Sequence):
            # join together two sequences
            other = other.rules
        else:
            # append other to this sequence
            other = (other,)
        return Sequence(*self.rules, *other)

    def __radd__(self, other):
        """Prepend another rule to the sequence.

        :param other: rule to prepend
        :returns: `Sequence`
        """
        other = ensure_rule(other)
        if isinstance(other, Sequence):
            # join together two sequences
            other = other.rules
        else:
            # prepend other to this sequence
            other = (other,)
        return Sequence(*other, *self.rules)

    def __mul__(self, other):
        """Append another rule to the sequence.

        Whitespace between rules will be ignored.

        :param other: rule to append
        :returns: `Sequence`
        """
        other = ensure_rule(other)
        if isinstance(other, Sequence):
            # join together two sequences
            other = other.rules
        else:
            # append other to this sequence
            other = (other,)
        return Sequence(*self.rules, WS(), *other)

    def __rmul__(self, other):
        """Prepend another rule to the sequence.

        Whitespace between rules will be preserved.

        :param other: rule to prepend
        :returns: `Sequence`
        """
        other = ensure_rule(other)
        if isinstance(other, Sequence):
            # join together two sequences
            other = other.rules
        else:
            # prepend other to this sequence
            other = (other,)
        return Sequence(*other, WS(), *self.rules)


class Alternatives(Rule):
    """Rule matching one of a set of alternatives."""

    def __init__(self, *rules):
        """Initializer.

        :param rules: rules to match
        """
        super(Alternatives, self).__init__()
        self.rules = tuple(ensure_rule(rule) for rule in rules)

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '({rules})'.format(
            rules=' | '.join(map(repr, self.rules)),
        )

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        :raises: `NoMatchError`
        """
        for i, rule in enumerate(self.rules):
            try:
                iter_context = rule.parse(s, context=context.copy())
            except NoMatchError:
                continue
            if (s == iter_context._unparsed) and (i + 1 < len(self.rules)):
                raise RuntimeError('Zero-length match in non-final Alternatives rule at {s!r}'.format(
                    s=s,
                ))
            return iter_context
        raise NoMatchError(rule=self, unparsed=s)

    def __or__(self, other):
        """Append a rule to the list of alternatives.

        :param other: rule to append
        :returns: `Alternatives`
        """
        other = ensure_rule(other)
        return Alternatives(*(self.rules + (other,)))

    def __ror__(self, other):
        """Prepend a rule to the list of alternatives.

        :param other: rule to prepend
        :returns: `Alternatives`
        """
        other = ensure_rule(other)
        return Alternatives(*((other,) + self.rules))


class Reference(Rule):
    """Dynamic reference to a rule.

    This is necessary for self-referential rules.
    """

    def __init__(self, fn):
        super(Reference, self).__init__()
        self.fn = fn

    def __repr__(self):
        """Render representation."""
        return '<Ref>'

    def parse(self, s, context):
        """Parse a string into the parse context.

        :param s: string to parse
        :param context: parse context
        :returns: `Context`
        """
        return self.fn(context).parse(s, context=context)


# shorthand names

Alt = Alternatives
Ch = Chars
L = Literal
LC = LiteralCS
Ref = Reference
Rx = RegExp
Seq = Sequence
