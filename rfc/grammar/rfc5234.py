"""Augmented BNF for Syntax Specifications: ABNF.

https://tools.ietf.org/html/rfc5234
"""
from ..parse import *


class C:
    """Constants."""

    CR = chr(0x0D)
    LF = chr(0x0A)
    CRLF = CR + LF
    DQUOTE = '"'
    HTAB = '\t'
    SP = ' '


class ABNF:
    """ABNF grammar rules."""

    class R:
        """Character ranges."""

        ALPHA = CharRange('a', 'z') | CharRange('A', 'Z')
        BIT = CharRange('01')
        CHAR = CharRange(0x01, 0x7F)
        CTL = CharRange(0x00, 0x1F) | 0x7F
        DIGIT = CharRange('0', '9')
        CR = CharRange(C.CR)
        LF = CharRange(C.LF)
        DQUOTE = CharRange(C.DQUOTE)
        HEXDIG = DIGIT | CharRange('abcdefABCDEF')
        HTAB = CharRange(C.HTAB)
        SP = CharRange(C.SP)
        VCHAR = CharRange('!', '~')
        OCTET = CharRange(0x00, 0xFF)

    ALPHA = Ch(R.ALPHA)
    BIT = Ch(R.BIT)
    CHAR = Ch(R.CHAR)                   # any 7-bit US-ASCII character, excluding NUL
    CR = L(C.CR)                        # carriage return
    LF = L(C.LF)                        # linefeed
    CRLF = L(C.CRLF)                    # Internet standard newline
    CTL = Ch(R.CTL)                     # controls
    DIGIT = Ch(R.DIGIT)                 # 0-9
    DQUOTE = L(C.DQUOTE)                # " (Double quote)
    HEXDIG = Ch(R.HEXDIG)
    HTAB = L(C.HTAB)                    # horizontal tab
    SP = L(C.SP)
    WSP = SP | HTAB                     # white space
    LWSP = (WSP | CRLF + WSP)[:]        # Use of this linear-white-space rule
                                        #  permits lines containing only white
                                        #  space that are no longer legal in
                                        #  mail headers and have caused
                                        #  interoperability problems in other
                                        #  contexts.
                                        # Do not use when defining mail
                                        #  headers and use with caution in
                                        #  other contexts.
    VCHAR = Ch(R.VCHAR)                 # visible (printing) characters
    OCTET = Ch(R.OCTET)                 # 8 bits of data