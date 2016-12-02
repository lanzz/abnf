"""Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing.

https://tools.ietf.org/html/rfc7230
"""
from ..parse import *
from .rfc3986 import URI
from .rfc5234 import ABNF


class HTTP:
    """HTTP grammar rules."""

    class R:
        """Character ranges."""

        tchar = CharRange('''!#$%&'*+-.^_`|~''') | ABNF.R.DIGIT | ABNF.R.ALPHA
        obs_text = CharRange(0x80, 0xFF)

    tchar = Ch(R.tchar)
    token = tchar[1:]
    method = token
    segment = URI.segment
    absolute_path = ('/' + segment)[1:]
    query = URI.query
    origin_form = absolute_path + ~('?' + query)
    absolute_URI = URI.absolute_URI
    absolute_form = absolute_URI
    authority = URI.authority
    authority_form = authority
    asterisk_form = L('*')
    request_target = origin_form | absolute_form | authority_form | asterisk_form
    HTTP_name = LC('HTTP')
    HTTP_version = HTTP_name + '/' + ABNF.DIGIT + '.' + ABNF.DIGIT
    request_line = method + ABNF.SP + request_target + ABNF.SP + HTTP_version + ABNF.CRLF
    status_code = ABNF.DIGIT[3]
    reason_phrase = Ch(ABNF.R.HTAB | ABNF.R.SP | ABNF.R.VCHAR | R.obs_text)[:]
    status_line = HTTP_version + ABNF.SP + status_code + ABNF.SP + reason_phrase + ABNF.CRLF
    start_line = request_line | status_line
    field_name = token
    field_vchar = Ch(ABNF.R.VCHAR | R.obs_text)
    field_content = field_vchar[1:] + ~((Ch(ABNF.R.SP | ABNF.R.HTAB))[1:] + field_vchar[1:])
    obs_fold = ABNF.CRLF + Ch(ABNF.R.SP | ABNF.R.HTAB)[1:]
    field_value = (field_content | obs_fold)[:]
    OWS = Ch(ABNF.R.SP | ABNF.R.HTAB)[:]
    header_field = field_name + ':' + OWS + field_value + OWS
    message_body = Ch()[:]
    HTTP_message = start_line + (header_field + ABNF.CRLF)[:] + ABNF.CRLF + ~message_body
