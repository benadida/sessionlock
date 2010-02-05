"""
A Simple Interface to Sending Email

Ben Adida (ben@adida.net)
"""

from base import config
from smtplib import SMTP
from email.MIMEText import MIMEText
from email.Header import Header
from email.Utils import parseaddr, formataddr

SMTP_SERVER = config.SMTP_SERVER

def simple_send(recipient, sender, subject, body, reply_to=None):
    """Send an email.

    All arguments should be Unicode strings (plain ASCII works as well).

    Only the real name part of sender and recipient addresses may contain
    non-ASCII characters.

    The email will be properly MIME encoded and delivered though SMTP to
    localhost port 25.  This is easy to change if you want something different.

    The charset of the email will be the first one out of US-ASCII, ISO-8859-1
    and UTF-8 that can represent all the characters occurring in the email.
    """

    msg = createMessage(recipient, sender, subject, body, reply_to)

    # Send the message via SMTP to localhost:25
    smtp = SMTP(SMTP_SERVER)
    if config.SMTP_USER:
        smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        
    smtp.sendmail(sender, recipient, msg.as_string())
    smtp.quit()

def no_send(recipient, sender, subject, body, reply_to=None):
    msg = createMessage(recipient, sender, subject, body, reply_to)
    
    print "== CONFIG SAYS NOT TO SEND EMAIL, so here it is =="
    print msg.as_string()
    print "==================================================\n\n"
    
def createMessage(recipients, sender, subject, body, reply_to=None):

    # Header class is smart enough to try US-ASCII, then the charset we
    # provide, then fall back to UTF-8.
    header_charset = 'ISO-8859-1'

    # We must choose the body charset manually
    for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
        try:
            body.encode(body_charset)
        except UnicodeError:
            pass
        else:
            break

    # Split real name (which is optional) and email address parts
    sender_name, sender_addr = parseaddr(sender)
    reply_to_name, reply_to_addr = parseaddr(reply_to)

    recipient_names = []
    recipient_addrs = []
    for recipient in recipients.split(', '): 
        recipient_names.append(parseaddr(recipient)[0])
        recipient_addrs.append(parseaddr(recipient)[1])

    # We must always pass Unicode strings to Header, otherwise it will
    # use RFC 2047 encoding even on plain ASCII strings.
    sender_name = str(Header(unicode(sender_name), header_charset))
    reply_to_name = str(Header(unicode(reply_to_name), header_charset))
    for recipient_name in recipient_names:
        recipient_name = str(Header(unicode(recipient_name), header_charset))

    # Make sure email addresses do not contain non-ASCII characters
    sender_addr = sender_addr.encode('ascii')
    reply_to_addr = reply_to_addr.encode('ascii')
    for recipient_addr in recipient_addrs:
        recipient_addr = recipient_addr.encode('ascii')

    # Create the message ('plain' stands for Content-Type: text/plain)
    msg = MIMEText(body.encode(body_charset), 'plain', body_charset)
    msg['From'] = formataddr((sender_name, sender_addr))
    foo = [(recipient_names[i], recipient_addrs[i]) for i in range(len(recipient_names))]
    msg['To'] = ", ".join([formataddr(f) for f in foo])
    msg['Reply-To'] = formataddr((reply_to_name, reply_to_addr))
    msg['Subject'] = Header(unicode(subject), header_charset)

    return msg
    
# don't send email if config says not to
if not config.SEND_MAIL:
    simple_send = no_send
