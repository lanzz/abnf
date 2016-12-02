"""Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing.

Authority: https://tools.ietf.org/html/rfc7230
"""
from ..parse import *
from .rfc3986 import URI
from .rfc5234 import ABNF


OWS = Ch(ABNF.R.SP | ABNF.R.HTAB)[:]

def CSV(rule, min=1, max=None):
    """Comma-separated list of `rule`.

    Allows empty items (', foo, , bar, ').

    :param rule: rule to match
    :param min: minimum number of matches
    :param max: maximum number of matches
    """
    return (OWS + L(',') + OWS)[:] + rule[min:max:(OWS + L(',') + OWS)[1:]] + (OWS + L(',') + OWS)[:]


class HTTP:
    """HTTP grammar rules."""

    class R:
        """Character ranges."""

        tchar = CharRange('''!#$%&'*+-.^_`|~''') | ABNF.R.DIGIT | ABNF.R.ALPHA
        obs_text = CharRange(0x80, 0xFF)
        qdtext = ABNF.R.HTAB | ABNF.R.SP | '!' | CharRange('#', '[') | CharRange(']', '~') | obs_text
        ctext = ABNF.R.HTAB | ABNF.R.SP | CharRange('!', "'") | CharRange('*', '[') | CharRange(']', '~') | obs_text

    OWS = OWS
    BWS = OWS
    RWS = OWS[1:]

    # Imported rules
    absolute_URI = URI.absolute_URI
    authority = URI.authority
    fragment = URI.fragment
    path_abempty = URI.path_abempty
    port = URI.port
    query = URI.query
    relative_part = URI.relative_part
    segment = URI.segment
    uri_host = URI.host

    # Components of HTTP messages
    tchar = Ch(R.tchar)
    token = tchar[1:]
    method = token
    absolute_path = ('/' + segment)[1:]
    origin_form = absolute_path + ~('?' + query)
    absolute_form = absolute_URI
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
    field_content = field_vchar[1:][1::(Ch(ABNF.R.SP | ABNF.R.HTAB))[1:]]
    obs_fold = ABNF.CRLF + Ch(ABNF.R.SP | ABNF.R.HTAB)[1:]
    field_value = (field_content | obs_fold)[:]
    header_field = field_name + ':' + OWS + field_value + OWS
    message_body = Ch()[:]

    # Components of header values
    connection_option = token
    qdtext = Ch(R.qdtext)
    quoted_pair = L('\\') + Ch(ABNF.R.HTAB | ABNF.R.SP | ABNF.R.VCHAR | R.obs_text)
    quoted_string = ABNF.DQUOTE + (qdtext[1:] | quoted_pair)[:] + ABNF.DQUOTE
    transfer_parameter = token + BWS + '=' + BWS + (token | quoted_string)
    transfer_extension = token + (OWS + ';' + OWS + transfer_parameter)[:]
    transfer_coding = L('chunked') | L('compress') | L('deflate') | L('gzip') | transfer_extension
    rank = ('0' + ~('.' + ABNF.DIGIT[:3])) | ('1' + ~(Ch('0')[:3]))
    t_ranking = OWS + ';' + OWS + L('q=') + rank
    t_codings = L('trailers') | (transfer_coding + ~t_ranking)
    protocol_name = token
    protocol_version = token
    protocol = protocol_name + ~('/' + protocol_version)
    pseudonym = token
    received_protocol = ~(protocol_name + '/') + protocol_version
    received_by = (uri_host + ~(':' + port)) | pseudonym
    ctext = Ch(R.ctext)
    comment = L('(') + (ctext[1:] | quoted_pair | Ref(lambda: HTTP.comment))[:] + L(')')


    # Principal rules
    HTTP_message = start_line + (header_field + ABNF.CRLF)[:] + ABNF.CRLF + ~message_body
    http_URI = L('http://') + authority + path_abempty + ~('?' + query) + ~('#' + fragment)
    https_URI = L('https://') + authority + path_abempty + ~('?' + query) + ~('#' + fragment)
    partial_URI = relative_part + ~('?' + query)
    Connection = CSV(connection_option)
    Content_Length = ABNF.DIGIT[1:]
    Host = uri_host + ~(':' + port)
    TE = CSV(t_codings, min=0)
    Trailer = CSV(field_name)
    Transfer_Encoding = CSV(transfer_coding)
    Upgrade = CSV(protocol)
    Via = CSV(received_protocol + RWS + received_by + ~(RWS + comment))
