import base64
import platform
import smtplib
from email.message import EmailMessage

from urlmonitor.actionbase import Action

_NODE = platform.node()

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

    check_cfg_vars = [
        "smtp_server",
        "from_address",
        "smtp_encryption",
        "smtp_user",
        "smtp_password",
        "smtp_port",
    ]
    default_vars = {
        "from_address": "urlmonitor@{}".format(_NODE),
        "smtp_encryption": "",
        "smtp_user": "",
        "smtp_password": "",
        "smtp_port": 0,
    }

    def make_message(self, fromaddr, toaddr, subject, text):
        msg = EmailMessage()
        msg["From"] = fromaddr
        msg["To"] = toaddr
        msg["Subject"] = subject
        msg.set_content(text)
        return msg

    def send_msg(self, server, fromaddr, toaddr, msg):
        if self.smtp_port == 0:
            if self.smtp_encryption is None:
                port = 25
            else:
                port = 587
        else:
            port = self.smtp_port

        if self.smtp_encryption == "SSL":
            srv = smtplib.SMTP_SSL(server, port)
        else:
            srv = smtplib.SMTP(server, port)

        with srv:
            if self.smtp_encryption == "STARTTLS":
                srv.starttls()

            if self.smtp_user:
                passwd = base64.b64decode(self.smtp_password).decode()
                srv.login(self.smtp_user, passwd)
            srv.send_message(msg)

    def __call__(self, name, arglst, url, content, variables, log):
        hostname = _NODE
        fromaddr = "UrlMonitor Bot <noreply@destrangis.com>"
        subject = "URL Changed: " + url
        contents = _msg_pattern.format(url=url, host=hostname, **variables)
        msg = self.make_message(fromaddr, arglst, subject, contents)
        try:
            self.send_msg(self.smtp_server, fromaddr, arglst, msg)
        except smtplib.SMTPException as exc:
            log.error("{}: {}".format(name, exc))


action_object = _EmailAction()
