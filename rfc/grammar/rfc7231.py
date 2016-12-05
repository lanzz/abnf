"""Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content.

Authority: https://tools.ietf.org/html/rfc7231
"""

from .rfc5234 import ABNF
from .rfc7230 import HTTP


class HTTP(HTTP):
    """HTTP grammar rules."""

    # Imported ABNF rules
    ALPHA = ABNF.ALPHA
    CR = ABNF.CR
    CRLF = ABNF.CRLF
    CTL = ABNF.CTL
    DIGIT = ABNF.DIGIT
    DQUOTE = ABNF.DQUOTE
    HEXDIG = ABNF.HEXDIG
    HTAB = ABNF.HTAB
    LF = ABNF.LF
    OCTET = ABNF.OCTET
    SP = ABNF.SP
    VCHAR = ABNF.VCHAR

    # Imported HTTP rules
    BWS = HTTP.BWS
    OWS = HTTP.OWS
    RWS = HTTP.RWS
    URI_reference = HTTP.URI_reference
    absolute_URI = HTTP.absolute_URI
    comment = HTTP.comment
    field_name = HTTP.field_name
    partial_URI = HTTP.partial_URI
    quoted_string = HTTP.quoted_string
    token = HTTP.token
