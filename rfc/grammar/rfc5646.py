"""Tags for Identifying Languages.

Authority: https://tools.ietf.org/html/rfc5646
"""
from ..parse import *
from .rfc5234 import ABNF


class C:
    """Constants."""

    irregular = [
        "en-GB-oed",        # irregular tags do not match
        "i-ami",            # the 'langtag' production and
        "i-bnn",            # would not otherwise be
        "i-default",        # considered 'well-formed'
        "i-enochian",       # These tags are all valid,
        "i-hak",            # but most are deprecated
        "i-klingon",        # in favor of more modern
        "i-lux",            # subtags or subtag
        "i-mingo",          # combination
        "i-navajo",
        "i-pwn",
        "i-tao",
        "i-tay",
        "i-tsu",
        "sgn-BE-FR",
        "sgn-BE-NL",
        "sgn-CH-DE",
    ]
    regular = [
        "art-lojban",       # these tags match the 'langtag'
        "cel-gaulish",      # production, but their subtags
        "no-bok",           # are not extended language
        "no-nyn",           # or variant subtags: their meaning
        "zh-guoyu",         # is defined by their registration
        "zh-hakka",         # and all of these are deprecated
        "zh-min",           # in favor of a more modern
        "zh-min-nan",       # subtag or sequence of subtags
        "zh-xiang",
    ]


class LangTag:
    """Language Tag grammar rules."""

    class R:
        """Character ranges."""

        # Imported ABNF ranges
        ALPHA = ABNF.R.ALPHA
        DIGIT = ABNF.R.DIGIT

    # Imported ABNF rules
    ALPHA = ABNF.ALPHA
    DIGIT = ABNF.DIGIT

    extlang = (ALPHA[3] +                               # selected ISO 639 codes
                    ~(L('-') + ALPHA[3])[:2])           # permanently reserved
    language = ((ALPHA[2:3] +                           # shortest ISO 639 code
                    ~(L('-') + extlang)) |              # sometimes followed by extended language subtags
                 ALPHA[4] |                             # or reserved for future usage
                 ALPHA[5:8])                            # or registered language subtag
    script = ALPHA[4]                                   # ISO 15924 code
    region = (ALPHA[2] |                                # ISO 3166-1 code
              DIGIT[3])                                 # UN M.49 code
    alphanum = Ch(R.ALPHA | R.DIGIT)
    variant = (alphanum[5:8] | (DIGIT + alphanum[3]))   # registered variants
    singleton = Ch(R.ALPHA | R.DIGIT - CharRange('xX')) # Single alphanumerics; "x" reserved for private use
    extension = singleton + (L('-') + alphanum[2:8])[1:]
    privateuse = "x" + (L('-') + alphanum[1:8])[1:]
    langtag = language + ~(L('-') + script) + ~(L('-') + region) + (L('-') + variant)[:] + (L('-') + extension)[:] + ~(L('-') + privateuse)
    irregular = L(*C.irregular)
    regular = L(*C.regular)
    grandfathered = irregular | regular                 # non-redundant tags registered during the RFC 3066 era

    Language_Tag = (langtag |                           # normal language tags
                    privateuse |                        # private use tag
                    grandfathered)                      # grandfathered tags