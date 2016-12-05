"""Exceptions."""


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
