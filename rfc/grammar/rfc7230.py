"""Hypertext Transfer Protocol (HTTP/1.1): Message Syntax and Routing.

Authority: https://tools.ietf.org/html/rfc7230
"""
from ..parse import *
from .rfc3986 import URI
from .rfc5234 import ABNF


OWS = Ch(ABNF.R.SP | ABNF.R.HTAB)[:]

def CSV(rule, min=1, max=None, name=None):
    """Comma-separated list of `rule`.

    Allows empty items (', foo, , bar, ').

    :param rule: rule to match
    :param min: minimum number of matches
    :param max: maximum number of matches
    """
    rule = rule[min:max:(OWS + L(',') + OWS)[1:]]
    if name is not None:
        rule = rule[str(name)]
    return (OWS + L(',') + OWS)[:] + rule + (OWS + L(',') + OWS)[:]


class HTTP:
    """HTTP grammar rules."""

    class R:
        """Character ranges."""

        # Imported ABNF ranges
        ALPHA = ABNF.R.ALPHA
        DIGIT = ABNF.R.DIGIT
        HTAB = ABNF.R.HTAB
        SP = ABNF.R.SP
        VCHAR = ABNF.R.VCHAR

        tchar = CharRange('''!#$%&'*+-.^_`|~''') | DIGIT | ALPHA
        obs_text = CharRange(0x80, 0xFF)
        qdtext = HTAB | SP | '!' | CharRange('#', '[') | CharRange(']', '~') | obs_text
        ctext = HTAB | SP | CharRange('!', "'") | CharRange('*', '[') | CharRange(']', '~') | obs_text

    OWS = OWS
    BWS = OWS
    RWS = OWS[1:]

    # Imported ABNF rules
    CRLF = ABNF.CRLF
    DIGIT = ABNF.DIGIT
    DQUOTE = ABNF.DQUOTE
    HEXDIG = ABNF.HEXDIG
    SP = ABNF.SP

    # Imported URI rules
    absolute_URI = URI.absolute_URI
    authority = URI.authority
    fragment = URI.fragment
    path_abempty = URI.path_abempty
    port = URI.port
    query = URI.query
    relative_part = URI.relative_part
    segment = URI.segment
    uri_host = URI.host
    URI_reference = URI.URI_reference

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
    HTTP_version = HTTP_name + '/' + DIGIT + '.' + DIGIT
    request_line = method + SP + request_target + SP + HTTP_version + CRLF
    status_code = DIGIT[3]
    reason_phrase = Ch(R.HTAB | R.SP | R.VCHAR | R.obs_text)[:]
    status_line = HTTP_version + SP + status_code + SP + reason_phrase + CRLF
    start_line = request_line | status_line
    field_name = token
    field_vchar = Ch(R.VCHAR | R.obs_text)
    field_content = field_vchar[1:][1::(Ch(R.SP | R.HTAB))[1:]]
    obs_fold = CRLF + Ch(R.SP | R.HTAB)[1:]
    field_value = (field_content | obs_fold)[:]
    header_field = field_name + ':' + OWS + field_value + OWS
    message_body = Ch()[:]

    # Components of header values
    connection_option = token
    qdtext = Ch(R.qdtext)
    quoted_pair = L('\\') + Ch(R.HTAB | R.SP | R.VCHAR | R.obs_text)
    quoted_string = DQUOTE + (qdtext[1:] | quoted_pair)[:] + DQUOTE
    transfer_parameter = token + BWS + '=' + BWS + (token | quoted_string)
    transfer_extension = token + (OWS + ';' + OWS + transfer_parameter)[:]
    transfer_coding = L('chunked') | L('compress') | L('deflate') | L('gzip') | transfer_extension
    rank = ('0' + ~('.' + DIGIT[:3])) | ('1' + ~(Ch('0')[:3]))
    t_ranking = OWS + ';' + OWS + L('q=') + rank
    t_codings = L('trailers') | (transfer_coding + ~t_ranking)
    protocol_name = token
    protocol_version = token
    protocol = protocol_name + ~('/' + protocol_version)
    pseudonym = token
    received_protocol = ~(protocol_name + '/') + protocol_version
    received_by = (uri_host + ~(':' + port)) | pseudonym
    ctext = Ch(R.ctext)
    comment = L('(') + (ctext[1:] | quoted_pair | Ref(lambda ctx: HTTP.comment))[:] + L(')')

    # Chunked encoding
    chunk_size = HEXDIG[1:]
    chunk_ext_name = token
    chunk_ext_val = token | quoted_string
    chunk_ext = (L(';') + chunk_ext_name + ~(L('=') + chunk_ext_val))[:]
    chunk_data = Ch()[:]
    chunk = chunk_size + ~chunk_ext + CRLF + chunk_data + CRLF
    last_chunk = Ch('0')[1:] + ~chunk_ext + CRLF
    trailer_part = header_field[:] + CRLF
    chunked_body = chunk[:] + last_chunk + trailer_part + CRLF

    # Principal rules
    HTTP_message = start_line + (header_field + CRLF)[:] + CRLF + ~message_body
    http_URI = L('http://') + authority + path_abempty + ~('?' + query) + ~('#' + fragment)
    https_URI = L('https://') + authority + path_abempty + ~('?' + query) + ~('#' + fragment)
    partial_URI = relative_part + ~('?' + query)
    Connection = CSV(connection_option)
    Content_Length = DIGIT[1:]
    Host = uri_host + ~(':' + port)
    TE = CSV(t_codings, min=0)
    Trailer = CSV(field_name)
    Transfer_Encoding = CSV(transfer_coding)
    Upgrade = CSV(protocol)
    Via = CSV(received_protocol + RWS + received_by + ~(RWS + comment))
