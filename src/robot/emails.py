import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPAuthenticationError
from email.message import EmailMessage
# import traceback
import re
import logging
from newAgent.src.robot.scraper import LogWrapper




class Email:
    """Using SMTP Protocol to sending email from an user or company to a person"""

    # Variables
    email_sender: str = ''
    password: str = ''
    name = 'email'
    _server = None
    logger: str = ''
    email_username: str = ''
    email_domain: str = ''
    isLoggedIn: bool = False
    function_result: str = ''
    result = None
    _max_retries: int = 3
    _retry: int = 0

    def __init__(self):
        self.logger = LogWrapper(logging.getLogger(__name__))

    # SMTP Variables
    #     icloud
    #     gmail
    #     yahoo
    #     hotmail
    #     outlook
    #     zoho
    #     aol
    #     hush mail
    #     ProtonMail
    #     yandex
    #     Neo
    #     GMX
    #     Fast mail

    _dict_email_provider: dict = {'gmail': ['smtp.gmail.com', 587],
                                  'icloud': ['smtp.mail.me.com', 587],
                                  'yahoo': ['smtp.mail.yahoo.com', 465],
                                  'hotmail': ['smtp.office365.com', 587],
                                  'outlook': ['smtp-mail.outlook.com', 587],
                                  'zoho': ['smtp.zoho.com', 465],
                                  'aol': ['smtp.aol.com', 465],
                                  'hushmail': ['smtp.hushmail.com', 587],
                                  'protonmail': ['smtp.protonmail.ch', 587],
                                  'yandex': ['smtp.yandex.com', 465],
                                  'neo': ['smtp0001.neo.space', 465],
                                  'gmx': ['mail.gmx.com', 465],
                                  'fastmail': ['smtp.fastmail.com', 587]}

    # SMTP return codes

    _smtp_code = {211: 'System status, or system help reply',
                  214: 'Help message (A response to the HELP command)',
                  220: '<domain> Service ready',
                  221: '<domain> Service closing transmission channel',
                  235: 'Authentication succeeded',
                  240: 'QUIT',
                  250: 'Requested mail action okay, completed',
                  251: 'User not local; will forward',
                  252: 'Cannot verify the user, but it will try to deliver the message anyway',

                  334: '(Server challenge - the text part contains the Base64-encoded challenge)',
                  354: 'Start mail input',

                  421: 'Service not available, closing transmission channel (This may be a reply to any command if the service knows it must shut down)',
                  432: 'A password transition is needed',
                  450: 'Requested mail action not taken: mailbox unavailable (e.g., mailbox busy or temporarily blocked for policy reasons)',
                  451: 'Requested action aborted: local error in processing',
                  452: 'Requested action not taken: insufficient system storage',
                  454: 'Temporary authentication failure',
                  455: 'Server unable to accommodate parameters',

                  500: 'Syntax error, command unrecognized (This may include errors such as command line too long)',
                  501: 'Syntax error in parameters or arguments',
                  502: 'Command not implemented',
                  503: 'Bad sequence of commands',
                  504: 'Command parameter is not implemented',
                  521: 'Server does not accept mail',
                  523: 'Encryption Needed',
                  530: 'Authentication required',
                  534: 'Authentication mechanism is too weak',
                  535: 'Authentication credentials invalid',
                  538: 'Encryption required for requested authentication mechanism',
                  550: 'Requested action not taken: mailbox unavailable (e.g., mailbox not found, no access, or command rejected for policy reasons)',
                  551: 'User not local; please try <forward-path>',
                  552: 'Requested mail action aborted: exceeded storage allocation',
                  553: 'Requested action not taken: mailbox name not allowed',
                  554: 'Message too big for system',
                  556: 'Domain does not accept mail'}

    @staticmethod
    def _extract_email(value):
        """private func for finding emails from txtInput --> dict"""
        ret: dict = {'status': None,
                     'message': '',
                     'values': [None, None]}
        try:
            match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', value)
            email_sender = match.group(0)
            idx_at = email_sender.index('@')
            provider_till_end = email_sender[idx_at + 1:]
            idx_dot = provider_till_end.index('.')
            provider = provider_till_end[:idx_dot]
            ret['values'] = email_sender.lower(), provider.lower()
            ret['status'] = True
            ret['message'] = '_extract_email Done successful'

        except Exception as e:
            ret['message'] = f'Something went wrong at _extract_email func! {e}'
            ret['status'] = False
        finally:
            return ret

    def login(self, email: str, password: str):
        """login from user via SMTP protocol, first we generate email and provider from input then send this to SMTP protocol"""
        ret: dict = {'status': None,
                     'message': '',
                     'values': None}
        try:
            self.logger += 'getting email domain...\n'
            ret = self._extract_email(email)
            self.logger.info(f'RET is {ret}')
            self.logger += ret['message'] + '\n'
            self.email_username, self.email_domain = ret['values']
            new_email_sender, provider = ret['values']
            SMTP_HOST, SMTP_PORT = self._dict_email_provider.get(provider, ['smtp.gmail.com', 587])
            if SMTP_HOST is None and SMTP_PORT is None:
                ret['status'] = False
                ret['message'] = f"Sorry we don't support this {provider} email provider"
                return ret
            elif SMTP_PORT == 465:
                self._server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
            elif SMTP_PORT == 587:
                self._server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
                self._server.starttls()

            self.email_sender = new_email_sender
            self.password = password
            res = self._server.login(self.email_sender, password)
            ret['status'] = True
            ret['message'] = res[1].decode('utf-8')
            ret['values'] = res[0]

        except SMTPAuthenticationError as smtp_err:

            ret['status'] = False
            ret['message'] = smtp_err.smtp_error.decode('utf-8')
            ret['values'] = smtp_err.smtp_code

        except Exception as e:
            ret['message'] = f'Something went wrong at email login func! {e}'
            ret['status'] = False
        finally:
            self.logger += ret['message'] + '\n'
            self.isLoggedIn = ret['status']
            return ret

    def sending_message(self, email_receive, subject, msg_text):
        """Sending Email func using EmailMessage template --> status, message, values"""
        self.function_result = ''
        if '</html>' in msg_text:
            return self.sending_html(email_receive, subject, msg_text)
        ret: dict = {'status': None,
                     'message': '',
                     'values': None}
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = email_receive
            msg.set_content(msg_text)
            self.logger += f'trying to compose message to {email_receive}\n'
            ret['values'] = self._server.sendmail(self.email_sender, email_receive, msg.as_string())
            ret['status'] = True
            ret['message'] = 'Sending email_invite has been successful.'
            self._retry = 0
            self.function_result = f'Message has been sent to {email_receive}.'
        except smtplib.SMTPServerDisconnected:
            if self._retry <= self._max_retries:
                self.logger.info(f'Trying login again at email number {self._retry}')
                self._retry += 1
                self.login(self.email_sender, self.password)
                ret = self.sending_message(email_receive, subject, msg_text)
                return ret
            ret['status'] = False
            ret['message'] = f'Something went wrong at Email.sending_message Error: Disconnected from server.'
            self.function_result = f"Can't send message to {email_receive} Error:  Disconnected from server"
        except Exception as e:
            ret['status'] = False
            ret['message'] = f'Something went wrong at Email.sending_message func. {e}'
            self.function_result = f"Can't send message to {email_receive} Error: {e}"
        finally:
            self.logger += ret['message'] + '\n'
            return ret

    def sending_html(self, email_receive, subject, html_content):
        """Sending Email via html css template"""
        ret: dict = {'status': None,
                     'message': '',
                     'values': None}
        try:

            # Define the email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_sender
            msg['To'] = email_receive

            # Add the HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            self.logger += f'trying to compose message to {email_receive}\n'
            ret['values'] = self._server.sendmail(self.email_sender, email_receive, msg.as_string())
            ret['status'] = True
            ret['message'] = 'Sending email_invite has been successful.'
            self.function_result = f'Message has been sent to {email_receive}.'
            self._retry = 0
        except smtplib.SMTPServerDisconnected:
            if self._retry <= self._max_retries:
                self.logger.info(f'Trying login again at email number {self._retry}')
                self._retry += 1
                self.login(self.email_sender, self.password)
                ret = self.sending_html(email_receive, subject, html_content)
                return ret
            ret['status'] = False
            ret['message'] = f'Something went wrong at Email.sending_html Error: Disconnected from server.'
            self.function_result = f"Can't send message to {email_receive} Error:  Disconnected from server"
        except Exception as e:
            ret['status'] = False
            ret['message'] = f'Something went wrong at Email.sending_message func. {e}'
            self.function_result = f"Can't send message to {email_receive} Error: {e}"
        finally:
            self.logger += ret['message'] + '\n'
            return ret

    def logout(self):
        try:
            self.logger.clear()
            self.isLoggedIn = False
            self._server.quit()
        except Exception as e:
            self.logger.error(e)


if __name__ == "__main__":
    mail = Email()
    mail.logger.info(mail.login('n.e.a.r.n.o10@gmail.com', 'eedb znbx bgqc sknf '))
    mail.logger.info(mail.sending_message('nokhodian@gmail.com', 'Hello There', '''Hello this is a test'''))
