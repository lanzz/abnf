"""Matching of Language Tags.

Authority: https://tools.ietf.org/html/rfc4647
"""
from ..parse import *
from .rfc5234 import ABNF


class LangRange:
    """Language Range grammar rules."""

    class R:
        """Character ranges."""

        # Imported ABNF ranges
        ALPHA = ABNF.R.ALPHA
        DIGIT = ABNF.R.DIGIT

    # Imported ABNF rules
    ALPHA = ABNF.ALPHA

    alphanum = Ch(R.ALPHA | R.DIGIT)
    language_range = (ALPHA[1:8] + (L('-') + alphanum[1:8])[:]) | L('*')
    extended_language_range = (ALPHA[1:8] | L('*')) + (L('-') + (alphanum[1:8] | L('*')))[:]
