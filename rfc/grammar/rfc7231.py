"""Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content.

Authority: https://tools.ietf.org/html/rfc7231
"""

from .rfc7230 import HTTP


class HTTP(HTTP):
    """HTTP grammar rules."""

    # Imported rules
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