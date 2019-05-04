import platform
import smtplib
from email.message import EmailMessage

from urlmonitor.actionbase import Action

_msg_pattern = """
The Python UrlMonitor application running on {host} is happy to
report that the following url:

{url}

Has been modified since {lastchecked} when it was last checked.

       | STATUS | CHECKSUM                         |
-------|--------|----------------------------------|
Former | {laststatus:^6} | {lastchecksum:<32} |
New    | {status:^6} | {checksum:<32} |

Kindest regards,

The UrlMonitor Bot

BTW Do not reply to this message -- it will not compute.
"""

class _EmailAction(Action):

    check_cfg_vars = [ "smtp_server" ]
    default_vars = {}

    def make_message(self, fromaddr, toaddr, subject, text):
        msg = EmailMessage()
        msg["From"] = fromaddr
        msg["To"] = toaddr
        msg["Subject"] = subject
        msg.set_content(text)
        return msg


    def send_msg(self, server, fromaddr, toaddr, msg):
        with smtplib.SMTP(server) as s:
            s.send_message(msg)


    def __call__(self, name, arglst, url, content, variables, log):
        hostname = platform.node()
        fromaddr = "UrlMonitor Bot <noreply@destrangis.com>"
        subject = "URL Changed: " + url
        contents = _msg_pattern.format(url=url, host=hostname, **variables)
        msg = self.make_message(fromaddr, arglst, subject, contents)
        self.send_msg(self.smtp_server, fromaddr, arglst, msg)


action_object = _EmailAction()
