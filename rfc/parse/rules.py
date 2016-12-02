import re

from .containers import CaptureDict, Match


__all__ = [
    'Alternatives',
    'Chars',
    'Literal',
    'LiteralCS',
    'RegExp',
    'Sequence',
    'Alt', 'Ch', 'L', 'LC', 'Rx', 'Seq',
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


class Rule(object):
    """Base class for all parser rules."""

    def parse(self, s):
        """Parse a string into a `Match` instance.

        :param s: string to parse
        :returns: `Match` or None
        """
        # by default, do not match anything
        return None

    def __call__(self, s, partial=False):
        """Parse a string and return its values.

        :param s: string to parse
        :param partial: boolean indicating whether to accept a partial match at start of ``s``
        """
        match = self.parse(s)
        if match and match.unparsed and not partial:
            match = None
        if not match:
            raise NoMatchError
        return match.captures

    def __getitem__(self, item):
        """Item accessor.

        rule['foo']     => capture the rule as "foo"
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
        if isinstance(item, str):
            # capture
            from .wrappers import Capture
            return Capture(self, item)
        reps = None
        if isinstance(item, int):
            # exact repetitions
            reps = dict(min=item, max=item)
        elif isinstance(item, slice):
            if (item.start or 0, item.stop, item.step) == (0, 1, None):
                # optional
                from .wrappers import Optional
                return Optional(self)
            # range of repetitions
            reps = dict(
                min=item.start or 0,
                max=item.stop,
                delimiter=item.step
            )
        if reps:
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

        Whitespace between rules will be preserved.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(self, other, ws=False)

    def __radd__(self, other):
        """Combine other and self into a `Sequence`.

        Whitespace between rules will be preserved.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(other, self, ws=False)

    def __mul__(self, other):
        """Combine self and other into a `Sequence`.

        Whitespace between rules will be ignored.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(self, other, ws=True)

    def __rmul__(self, other):
        """Combine other and self into a `Sequence`.

        Whitespace between rules will be ignored.

        :returns: `Sequence`
        """
        other = ensure_rule(other)
        return Sequence(other, self, ws=True)

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


class Literal(Rule):
    """Rule matching a literal string.

    Case-insensitive by default; pass casefold=False or use the
    LiteralCS alternate constructor for case-sensitive match.
    """

    def __init__(self, literal, casefold=None):
        """Initializer.

        :param literal: literal string to match
        :param casefold: boolean indicating if matching should be case-folded
        """
        super(Literal, self).__init__()
        self.casefold = True if casefold is None else casefold
        if self.casefold:
            literal = literal.casefold()
        self.literal = literal
        self.len = len(self.literal)

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        return '<Literal {literal!r}{casefold}>'.format(
            literal=self.literal,
            casefold=' (nocase)' if self.casefold else ' (case)',
        )

    def parse(self, s):
        """Parse a string.

        :param s: string to parse
        :returns: `Match` or None
        """
        cs = s.casefold() if self.casefold else s
        if not cs.startswith(self.literal):
            return None
        value = s[:self.len]
        value = value.casefold() if self.casefold else value
        return Match(value=value, unparsed=s[self.len:])


def LiteralCS(literal):
    """Rule matching a case-sensitive literal.

    :param literal: literal string to match
    :param args: arguments to pass through to `Literal`
    :param kwargs: keyword arguments to pass through to `Literal`
    :returns: `Literal`
    """
    return Literal(literal, casefold=False)


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

    def parse(self, s):
        """Parse a string.

        Named groups will be extracted as captures.

        :param s: string to parse
        :returns: `Match` or None
        """
        m = self.regexp.match(s)
        if not m:
            return None
        value = m.group(0)
        captures = m.groupdict()
        return Match(value=value, captures=captures, unparsed=s[len(value):])


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
        return '<Chars [{len}] {chars}{exclude}>'.format(
            len=self.min if self.min == self.max else '{min}..{max}'.format(
                min=self.min,
                max=self.max if self.max is not None else 'inf',
            ),
            chars='{chars!r}'.format(
                chars=''.join(sorted(self.chars)),
            ) if self.chars is not None else '',
            exclude='-{exclude!r}'.format(
                exclude=self.exclude,
            ) if self.exclude is not None else '',
        )

    def parse(self, s):
        """Parse a string.

        :param s: string to parse
        :returns: `Match` or None
        """
        if self.chars is self.exclude is None:
            # match anything
            match = len(s)
        else:
            match = 0
            if len(s):
                for match, c in enumerate(s):
                    if not self._predicate(c):
                        break
                else:
                    match += 1
        if self.max is not None:
            match = min(match, self.max)
        if match < self.min:
            # not enough matching characters
            return None
        value = s[:match]
        return Match(value, unparsed=s[match:])

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
        elif isinstance(item, slice) and item.step is None:
            # only return a copy if slice has no step;
            # slice step is the delimiter for a Repeat rule
            overrides = dict(min=item.start or 0, max=item.stop)
        if overrides:
            return Chars(self.chars, self.exclude, **overrides)
        else:
            return super(Chars, self).__getitem__(item)


class Sequence(Rule):
    """Rule matching a sequence of rules in order."""

    def __init__(self, *rules, ws=True):
        """Initializer.

        :param rules: rules to match
        :param ws: if true, whitespace between rules will be stripped
        """
        super(Sequence, self).__init__()
        self.rules = tuple(ensure_rule(rule) for rule in rules)
        self.ws = ws

    def __repr__(self):
        """Render representation.

        :returns: str
        """
        op = ' * ' if self.ws else ' + '
        return '<Seq {rules}>'.format(
            rules=op.join(map(repr, self.rules)),
        )

    def parse(self, s):
        """Parse a string.

        :param s: string to parse
        :returns: `Match` or None
        """
        matches = []
        remainder = s
        for rule in self.rules:
            match = rule.parse(remainder.lstrip() if (matches and self.ws) else remainder)
            if not match:
                return None
            matches.append(match)
            remainder = match.unparsed
        value = ''.join(match.str_value for match in matches)
        captures = CaptureDict(
            kv
            for match in matches
            for kv in match.captures.items()
        )
        return Match(value=value, captures=captures, unparsed=remainder)

    def __add__(self, other):
        """Append another rule to the sequence.

        Whitespace between rules will be preserved.

        :param other: rule to append
        :returns: `Sequence`
        """
        if self.ws:
            # this sequence ignores whitespace, can't combine
            return super(Sequence, self).__add__(other)
        other = ensure_rule(other)
        if isinstance(other, Sequence) and other.ws:
            # join together two compatible sequences
            other = Sequence.rules
        else:
            # append other to this sequence
            other = (other,)
        return Sequence(*(self.rules + other), ws=False)

    def __radd__(self, other):
        """Prepend another rule to the sequence.

        Whitespace between rules will be preserved.

        :param other: rule to prepend
        :returns: `Sequence`
        """
        if self.ws:
            # this sequence ignores whitespace, can't combine
            return super(Sequence, self).__radd__(other)
        other = ensure_rule(other)
        if isinstance(other, Sequence) and other.ws:
            # join together two compatible sequences
            other = Sequence.rules
        else:
            # prepend other to this sequence
            other = (other,)
        return Sequence(*(other + self.rules), ws=False)

    def __mul__(self, other):
        """Append another rule to the sequence.

        Whitespace between rules will be ignored.

        :param other: rule to append
        :returns: `Sequence`
        """
        if not self.ws:
            # this sequence preserves whitespace, can't combine
            return super(Sequence, self).__mul__(other)
        other = ensure_rule(other)
        if isinstance(other, Sequence) and not other.ws:
            # join together two compatible sequences
            other = Sequence.rules
        else:
            # append other to this sequence
            other = (other,)
        return Sequence(*(self.rules + other), ws=True)

    def __rmul__(self, other):
        """Prepend another rule to the sequence.

        Whitespace between rules will be preserved.

        :param other: rule to prepend
        :returns: `Sequence`
        """
        if not self.ws:
            # this sequence ignores whitespace, can't combine
            return super(Sequence, self).__rmul__(other)
        other = ensure_rule(other)
        if isinstance(other, Sequence) and not other.ws:
            # join together two compatible sequences
            other = Sequence.rules
        else:
            # prepend other to this sequence
            other = (other,)
        return Sequence(*(other + self.rules), ws=True)


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
        return '<Alt {rules}>'.format(
            rules=' | '.join(map(repr, self.rules)),
        )

    def parse(self, s):
        """Parse a string.

        :param s: string to parse
        :returns: `Match` or None
        """
        for rule in self.rules:
            match = rule.parse(s)
            if match:
                assert s != match.unparsed, 'Zero-length match in Alternatives rule: {rule!r}'.format(
                    rule=rule,
                )
                return match
        return None

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


# shorthand names

L = Literal
LC = LiteralCS
Ch = Chars
Rx = RegExp
Seq = Sequence
Alt = Alternatives