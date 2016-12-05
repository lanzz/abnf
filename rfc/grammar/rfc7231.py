"""Hypertext Transfer Protocol (HTTP/1.1): Semantics and Content.

Authority: https://tools.ietf.org/html/rfc7231
"""
from ..parse import *
from .rfc4647 import LangRange
from .rfc5234 import ABNF
from .rfc5322 import IMF
from .rfc5646 import LangTag
from .rfc7230 import CSV, HTTP


class C:
    """Constants."""

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names_l = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ]
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


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

    # Imported Internet Message Format rules
    mailbox = IMF.mailbox

    # Imported Language Range rules
    language_range = LangRange.language_range

    # Imported Language Tag rules
    language_tag = LangTag.Language_Tag

    # Components of header values
    type = token
    subtype = token
    parameter = token + L('=') + (token | quoted_string)
    media_range = (L('*/*') | (type + L('/*')) | (type + L('/') + subtype)) + (OWS + ';' + OWS + parameter)[:]
    qvalue = (L('0') + ~(L('.') + DIGIT[:3])) | (L('1') + ~(L('.') + Ch('0')[:3]))
    weight = OWS + ';' + OWS + L('q=') + qvalue
    accept_ext = OWS + ';' + OWS + token + ~(L('=') + (token | quoted_string))
    accept_params = weight + accept_ext[:]
    charset = token
    content_coding = token
    codings = content_coding | L('identity') | L('*')
    method = token
    media_type = type + L('/') + subtype + (OWS + L(';') + OWS + parameter)[:]
    day_name = LC(*C.day_names)
    day_name_l = LC(*C.day_names_l)
    day = DIGIT[2]
    month = LC(*C.months)
    year = DIGIT[4]
    date1 = day + SP + month + SP + year
    date2 = day + L('-') + month + L('-') + DIGIT[2]
    date3 = month + SP + (DIGIT[2] | (SP + DIGIT))
    hour = DIGIT[2]
    minute = DIGIT[2]
    second = DIGIT[2]
    time_of_day = hour + L(':') + minute + L(':') + second
    GMT = LC('GMT')
    IMF_fixdate = day_name + ',' + SP + date1 + SP + time_of_day + SP + GMT
    rfc850_date = day_name_l + ',' + SP + date2 + SP + time_of_day + SP + GMT
    asctime_date = day_name + ',' + SP + date3 + SP + time_of_day + SP + year
    obs_date = rfc850_date | asctime_date
    HTTP_date = IMF_fixdate | obs_date
    product_version = token
    product = token + ~(L('/') + product_version)

    # Principal rules
    Accept = CSV(media_range + ~accept_params, min=0)
    Accept_Charset = CSV((charset | L('*')) + ~weight)
    Accept_Encoding = CSV(codings + ~weight, min=0)
    Accept_Language = CSV(language_range + ~weight)
    Allow = CSV(method, min=0)
    Content_Encoding = CSV(content_coding)
    Content_Language = CSV(language_tag)
    Content_Location = absolute_URI | partial_URI
    Content_Type = media_type
    Date = HTTP_date
    Expect = L('100-continue')
    From = mailbox
    Location = URI_reference
    Max_Forwards = DIGIT[1:]
    Server = product + (RWS + (product | comment))[:]
    User_Agent = product + (RWS + (product | comment))[:]
    Vary = L('*') | CSV(field_name)