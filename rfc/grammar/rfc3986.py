"""Uniform Resource Identifier (URI): Generic Syntax.

Authority: https://tools.ietf.org/html/rfc3986
"""

from ..parse import *
from .rfc5234 import ABNF


class URI:
    """URI grammar rules."""

    class R:
        """Character ranges."""

        unreserved = ABNF.R.ALPHA | ABNF.R.DIGIT | CharRange('-._~')
        gen_delims = CharRange(':/?#[]@')
        sub_delims = CharRange("!$&'()*+,;=")
        reserved = gen_delims | sub_delims

    scheme = (ABNF.ALPHA + Ch(ABNF.R.ALPHA | ABNF.R.DIGIT | '+-.')[:])['scheme']
    pct_encoded = Ign('%') + XF(ABNF.HEXDIG[2], lambda v: chr(int(v, 16)))
    userinfo = +(Ch(R.unreserved | R.sub_delims)[1:] | pct_encoded | ':')[:]['userinfo']
    dec_octet = Assert(Ch('123456789') + ABNF.DIGIT[:2], lambda m: int(m) <= 255)
    IPv4address = dec_octet + '.' + dec_octet + '.' + dec_octet + '.' + dec_octet
    h16 = ABNF.HEXDIG[1:4]
    ls32 = (h16 + ':' + h16) | IPv4address
    IPv6address = ((                                  (h16 + ':')[6] + ls32)
                 | (                           '::' + (h16 + ':')[5] + ls32)
                 | (                           '::' + (h16 + ':')[4] + ls32)
                 | (~((h16 + ':')[:1] + h16) + '::' + (h16 + ':')[3] + ls32)
                 | (~((h16 + ':')[:2] + h16) + '::' + (h16 + ':')[2] + ls32)
                 | (~((h16 + ':')[:3] + h16) + '::' + (h16 + ':')[1] + ls32)
                 | (~((h16 + ':')[:4] + h16) + '::'                  + ls32)
                 | (~((h16 + ':')[:5] + h16) + '::'                  + h16 )
                 | (~((h16 + ':')[:6] + h16) + '::'                        ))
    IPvFuture = 'v' + ABNF.HEXDIG[1:] + '.' + (Ch(R.unreserved | R.sub_delims)[1:] | ':')[1:]
    IP_literal = '[' + (IPv6address | IPvFuture) + ']'
    reg_name = (Ch(R.unreserved | R.sub_delims)[1:] | pct_encoded)[:]
    host = +(IP_literal | IPv4address | reg_name)['host']
    port = ABNF.DIGIT[:]['port']
    authority = ~(userinfo + '@') + host + ~(':' + port)
    pchar = Ch(R.unreserved | R.sub_delims)[1:] | pct_encoded | Ch(':@')[1:]
    segment = pchar[:]
    segment_nz = pchar[1:]
    segment_nz_nc = (Ch(R.unreserved | R.sub_delims)[1:] | pct_encoded | '@')[1:]
    path_abempty = +('/' + segment)[:]['path']                          # begins with "/" or is empty
    path_absolute = ('/' + ~(segment_nz + ('/' + segment)[:]))['path']  # begins with "/" but not "//"
    path_noscheme = (segment_nz_nc + ('/' + segment)[:])['path']        # begins with a non-colon segment
    path_rootless = (segment_nz + ('/' + segment)[:])['path']           # begins with a segment
    path_empty = +pchar[0]['path']                                      # zero characters
    hier_part = (L('//') + authority + path_abempty) | path_absolute | path_rootless | path_empty
    query = +(pchar | Ch('/?')[1:])[:]['query']
    fragment = +(pchar | Ch('/?')[1:])[:]['fragment']
    relative_part = (L('//') + authority + path_abempty) | path_absolute | path_noscheme | path_empty
    relative_ref = relative_part + ~('?' + query) + ~('#' + fragment)

    URI = scheme + ':' + hier_part + ~('?' + query) + ~('#' + fragment)
    absolute_URI = scheme + ':' + hier_part + ~('?' + query)
    URI_reference = URI | relative_ref
