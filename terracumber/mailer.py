"""Manages sending email templates"""
import smtplib
from email.mime.text import MIMEText
from string import Template


class Mailer():
    """The Mailer class is used to send emails

    Keyword arguments:
    template - A string with the path where the email template is.
    from_addr - A string with the email address for From:
    to_addr - A string with the email address for To: (can include variables for templating)
    subject - A string with subject for the email
    variables - A dictonary with the variables for the template
    """

    def __init__(self, template, from_addr, to_addr, subject, variables):
        self.template = template
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.subject = subject
        self.msg = None
        self.variables = variables
        self.fill_template()

    def fill_template(self):
        """ Fill message and subject templates from a file with variables """
        with open(self.template, 'r') as template:
            self.msg = MIMEText(
                Template(template.read()).safe_substitute(self.variables))
        self.subject = Template(self.subject).safe_substitute(self.variables)
        return self.subject, self.msg

    def get_message(self):
        return self.msg

    def get_subject(self):
        return self.subject

    def send_email(self):
        ''' Sends an email '''
        self.msg['Subject'] = self.subject
        self.msg['From'] = self.from_addr
        self.msg['To'] = self.to_addr
        conn = smtplib.SMTP('localhost')
        conn.send_message(self.msg)
        conn.quit()
