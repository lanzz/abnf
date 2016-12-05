"""Internet Message Format.

Authority: https://tools.ietf.org/html/rfc5322
"""
from ..parse import *
from .rfc5234 import ABNF


class C:
    """Constants."""

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    obs_zones = [
        'UT', 'GMT',        # Universal Time
                            # North American UT
                            # offsets
        'EST', 'EDT',       # Eastern:  - 5/ - 4
        'CST', 'CDT',       # Central:  - 6/ - 5
        'MST', 'MDT',       # Mountain: - 7/ - 6
        'PST', 'PDT',       # Pacific:  - 8/ - 7
    ]


def obs_csv(rule, min=0, max=None):
    """Obsolete comma-separated list.

    Allows for empty elements and comments and folding whitespace.
    """
    CFWS = Ref(lambda ctx: IMF.CFWS)
    comma = (~CFWS + L(','))
    return comma[:] + ~CFWS + rule[min:max:comma[1:] + ~CFWS] + comma[:] + ~CFWS


class IMF:
    """Internet Message Format grammar rules."""

    class R:
        """Character ranges."""

        # Imported ABNF character ranges
        ALPHA = ABNF.R.ALPHA
        CR = ABNF.R.CR
        DIGIT = ABNF.R.DIGIT
        DQUOTE = ABNF.R.DQUOTE
        LF = ABNF.R.LF
        VCHAR = ABNF.R.VCHAR

        # Printable US-ASCII characters...
        atext = ALPHA | DIGIT | CharRange('!#$%&\'*+-/=?^_`{|}~')           # ...not including specials. Used for atoms.
        ctext = CharRange(33, 39) | CharRange(42, 91) | CharRange(93, 126)  # ...not including "(", ")", or "\"
        dtext = CharRange(33, 90) | CharRange(94, 126)                      # ...not including "[", "]", or "\"
        ftext = CharRange(33, 57) | CharRange(59, 126)                      # ...not including ":"
        qtext = CharRange(33) | CharRange(35, 91) | CharRange(93, 126)      # ...not including "\" or the quote character

        specials = CharRange('()<>[]:;@\,." /') | DQUOTE                    # Special characters that do not appear in atext
        text = CharRange(1, 9) | CharRange(11, 12) | CharRange(14, 127)     # Characters excluding CR and LF

        # US-ASCII control characters that do not include the carriage return, line feed, and
        # white space characters:
        obs_NO_WS_CTL = CharRange(1, 8) | CharRange(11, 12) | CharRange(14, 31) | CharRange(127)
        obs_ctext = obs_NO_WS_CTL
        obs_dtext = obs_NO_WS_CTL
        obs_qtext = obs_NO_WS_CTL
        obs_utext = CharRange(0) | obs_NO_WS_CTL | VCHAR

        obs_zone = (CharRange(65, 73) |                                     # Military zones - "A"
                    CharRange(75, 90) |                                     # through "I" and "K"
                    CharRange(97, 105) |                                    # through "Z", both
                    CharRange(107, 122))                                    # upper and lower case


    # Imported ABNF rules
    CR = ABNF.CR
    CRLF = ABNF.CRLF
    DIGIT = ABNF.DIGIT
    DQUOTE = ABNF.DQUOTE
    LF = ABNF.LF
    VCHAR = ABNF.VCHAR
    WSP = ABNF.WSP

    # 3.2.1. Quoted characters
    obs_qp = L('\\') + Ch(CharRange(0) | R.obs_NO_WS_CTL | R.LF | R.CR)
    quoted_pair = (L('\\') + (VCHAR | WSP)) | obs_qp

    # 3.2.2. Folding White Space and Comments
    obs_FWS = WSP[1:] + (CRLF + WSP[1:])[:]
    FWS = (~(WSP[:] + CRLF) + WSP[1:]) | obs_FWS            # folding white space
    ctext = Ch(R.ctext | R.obs_ctext)
    ccontent = ctext[1:] | quoted_pair | Ref(lambda ctx: IMF.comment)
    comment = L('(') + (~FWS + ccontent)[:] + ~FWS + L(')')
    CFWS = XF(((~FWS + comment)[1:] + ~FWS) | FWS, ' ')

    # 3.2.4. Quoted string
    qtext = Ch(R.qtext | R.obs_qtext)
    qcontent = qtext[1:] | quoted_pair
    quoted_string = ~CFWS + DQUOTE + (~FWS + qcontent)[:] + ~FWS + DQUOTE + ~CFWS

    # 3.2.3. Atom
    atext = Ch(R.atext)
    atom = ~CFWS + atext[1:] + ~CFWS
    dot_atom_text = atext[1:] + (L('.') + atext[1:])[:]
    dot_atom = ~CFWS + dot_atom_text + ~CFWS
    specials = Ch(R.specials)

    # 3.2.5. Miscellaneous Tokens
    word = atom | quoted_string
    obs_phrase = word + (word | L('.') | CFWS)[:]
    phrase = word[1:] | obs_phrase
    obs_phrase_list = ~(phrase | CFWS) + (L(',') + ~(phrase | CFWS))[:]
    obs_utext = Ch(R.obs_utext)
    obs_unstruct = ((LF[:] + CR[:] + (obs_utext + LF[:] + CR[:])[:]) | FWS)[:]
    unstructured = ((~FWS + VCHAR)[:] + WSP[:]) | obs_unstruct

    # 3.3. Date and time Specification
    day_name = L(*C.day_names)
    obs_day_of_week = ~CFWS + day_name + ~CFWS
    day_of_week = (~FWS + day_name) | obs_day_of_week
    obs_day = ~CFWS + DIGIT[1:2] + ~CFWS
    day = (~FWS + DIGIT[1:2] + FWS) | obs_day
    month = L(*C.months)
    obs_year = ~CFWS + DIGIT[2:] + ~CFWS
    year = (FWS + DIGIT[4:]) | obs_year
    date = day + month + year
    obs_hour = ~CFWS + DIGIT[2] + ~CFWS
    obs_minute = ~CFWS + DIGIT[2] + ~CFWS
    obs_second = ~CFWS + DIGIT[2] + ~CFWS
    hour = DIGIT[2] | obs_hour
    minute = DIGIT[2] | obs_minute
    second = DIGIT[2] | obs_second
    time_of_day = hour + L(':') + minute + ~(L(':') + second)
    obs_zone = L(*C.obs_zones) | Ch(R.obs_zone)
    zone = (FWS + Ch('+-') + DIGIT[4]) | obs_zone
    time = time_of_day + zone
    date_time = ~(day_of_week + L(',')) + date + time + ~CFWS

    # 3.4.1. Addr-Spec Specification
    obs_local_part = word + (L('.') + word)[:]
    local_part = dot_atom | quoted_string | obs_local_part
    obs_domain = atom + (L('.') + atom)[:]
    dtext = Ch(R.dtext | R.obs_dtext) | quoted_pair
    domain_literal = ~CFWS + L('[') + (~FWS + dtext)[:] + ~FWS + L(']') + ~CFWS
    domain = dot_atom | domain_literal | obs_domain
    addr_spec = (local_part + L('@') + domain)['addr_spec']

    # 3.4. Address Specification
    display_name = +phrase['display_name']
    obs_domain_list = obs_csv(L('@') + domain)
    obs_route = obs_domain_list + ':'
    obs_angle_addr = ~CFWS + L('<') + obs_route + addr_spec + L('>') + ~CFWS
    angle_addr = (~CFWS + L('<') + addr_spec + L('>') + ~CFWS) | obs_angle_addr
    name_addr = ~display_name + angle_addr
    mailbox = name_addr | addr_spec
    obs_mbox_list = obs_csv(mailbox)
    mailbox_list = mailbox[::L(',')] | obs_mbox_list
    obs_group_list = (~CFWS + L(','))[1:] + ~CFWS
    group_list = mailbox_list | CFWS | obs_group_list
    group = display_name + L(':') + ~group_list + L(';') + ~CFWS
    address = (mailbox | group)['address']
    obs_addr_list = obs_csv(address)
    address_list = address[::L(',')]['addresses'] | obs_addr_list

    # 3.6.1. Origination Date
    orig_date = L('Date:') + date_time

    # 3.6.2. Originator Fields
    from_ = L('From:') + mailbox_list + CRLF
    sender = L('Sender:') + mailbox + CRLF
    reply_to = L('Reply-To:') + address_list + CRLF

    # 3.6.3. Destination Address Fields
    to = L('To:') + address_list + CRLF
    cc = L('Cc:') + address_list + CRLF
    bcc = L('Bcc:') + ~(address_list | CFWS) + CRLF

    # 3.6.4. Identification Fields
    obs_id_left = local_part
    id_left = dot_atom_text | obs_id_left
    no_fold_literal = L('[') + dtext[:] + L(']')
    obs_id_right = domain
    id_right = dot_atom_text | no_fold_literal | obs_id_right
    msg_id = ~CFWS + L('<') + id_left + L('@') + id_right + L('>') + ~CFWS
    message_id = L('Message-ID:') + msg_id + CRLF
    in_reply_to = L('In-Reply-To:') + msg_id[1:] + CRLF
    references = L('References:') + msg_id[1:] + CRLF

    # 3.6.5. Informational Fields
    subject = L('Subject:') + unstructured + CRLF
    comments = L('Comments:') + unstructured + CRLF
    keywords = L('Keywords:') + phrase[::L(',')] + CRLF

    # 3.6.6. Resent Fields
    resent_date = L('Resent-Date:') + date_time + CRLF
    resent_from = L('Resent-From:') + mailbox_list + CRLF
    resent_sender = L('Resent-Sender:') + mailbox + CRLF
    resent_to = L('Resent-To:') + address_list + CRLF
    resent_cc = L('Resent-Cc:') + address_list + CRLF
    resent_bcc = L('Resent-Bcc:') + ~(address_list | CFWS) + CRLF
    resent_msg_id = L('Resent-Message-ID:') + msg_id + CRLF

    # 3.6.7. Trace Fields
    path = angle_addr | (~CFWS + L('<') + ~CFWS + L('>') + ~CFWS)
    received_token = word | angle_addr | addr_spec | domain
    return_ = L('Return-Path:') + path + CRLF
    received = L('Received:') + received_token[:] + L(';') + date_time + CRLF
    trace = ~return_ + received[1:]

    # 4.5.1. Obsolete Origination Date Field
    obs_orig_date = L('Date') + WSP[:] + ':' + date_time + CRLF

    # 4.5.2. Obsolete Originator Fields
    obs_from = L('From:') + WSP[:] + ':' + mailbox_list + CRLF
    obs_sender = L('Sender') + WSP[:] + ':' + mailbox + CRLF
    obs_reply_to = L('Reply_To') + WSP[:] + ':' + address_list + CRLF

    # 4.5.3. Obsolete Destination Address Fields
    obs_to = L('To:') + WSP[:] + ':' + address_list + CRLF
    obs_cc = L('Cc:') + WSP[:] + ':' + address_list + CRLF
    obs_bcc = L('Bcc:') + WSP[:] + ':' + (address_list | ((~CFWS + L(','))[:] + ~CFWS)) + CRLF

    # 4.5.4. Obsolete Identification Fields
    obs_message_id = L('Message-ID:') + WSP[:] + ':' + msg_id + CRLF
    obs_in_reply_to = L('In-Reply-To:') + WSP[:] + ':' + (phrase | msg_id)[:] + CRLF
    obs_references = L('References:') + WSP[:] + ':' + (phrase | msg_id)[:] + CRLF

    # 4.5.5. Obsolete Informational Fields
    obs_subject = L('Subject:') + WSP[:] + ':' + unstructured + CRLF
    obs_comments = L('Comments:') + WSP[:] + ':' + unstructured + CRLF
    obs_keywords = L('Keywords:') + WSP[:] + ':' + obs_phrase_list + CRLF

    # 4.5.6. Obsolete Resent Fields
    obs_resent_from = L('Resent-From') + WSP[:] + ':' + mailbox_list + CRLF
    obs_resent_send = L('Resent-Sender') + WSP[:] + ':' + mailbox + CRLF
    obs_resent_date = L('Resent-Date') + WSP[:] + ':' + date_time + CRLF
    obs_resent_to = L('Resent-To') + WSP[:] + ':' + address_list + CRLF
    obs_resent_cc = L('Resent-Cc') + WSP[:] + ':' + address_list + CRLF
    obs_resent_bcc = L('Resent-Bcc') + WSP[:] + ':' + (address_list | ((~CFWS + L(','))[:] + ~CFWS)) + CRLF
    obs_resent_mid = L('Resent-Message-ID') + WSP[:] + ':' + msg_id + CRLF
    obs_resent_rply = L('Resent-Reply-To') + WSP[:] + ':' + address_list + CRLF

    # 4.5.7. Obsolete Trace Fields
    obs_return = L('Return') + WSP[:] + ':' + path + CRLF
    obs_received = L('Received') + WSP[:] + ':' + received_token[:] + CRLF

    # 4.5.8. Obsolete Optional Fields
    obs_optional = Ref(lambda ctx: IMF.field_name) + WSP[:] + L(':') + unstructured + CRLF

    # 3.6. Field Definitions
    ftext = Ch(R.ftext)
    field_name = ftext[1:]
    optional_field = field_name + L(':') + unstructured + CRLF
    fields = (trace + optional_field[:] + (
        resent_date | resent_from | resent_sender |
        resent_to | resent_cc | resent_bcc | resent_msg_id
    )[:])[:] + (
        orig_date | from_ | sender | reply_to | to | cc | bcc | message_id |
        in_reply_to | references | subject | comments | keywords | optional_field
    )[1:]
    obs_fields = (
        obs_return | obs_received | obs_orig_date | obs_from | obs_sender | obs_reply_to |
        obs_to | obs_cc | obs_bcc | obs_message_id | obs_in_reply_to | obs_references |
        obs_subject | obs_comments | obs_keywords | obs_resent_date | obs_resent_from |
        obs_resent_send | obs_resent_rply | obs_resent_to | obs_resent_cc | obs_resent_bcc |
        obs_resent_mid | obs_optional
    )

    # 3.5. Overall Message Syntax
    text = Ch(R.text)
    obs_body = ((LF[:] + CR[:] + (Ch(CharRange(0) | R.text) + LF[:] + CR[:])[:]) | CRLF)[:]
    body = text[:998][::CRLF] | obs_body
    message = (fields | obs_fields) + ~(CRLF + body)
