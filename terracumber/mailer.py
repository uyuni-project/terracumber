import smtplib
from email.mime.text import MIMEText
from string import Template

class Mailer():
    ''' The Mailer class is used to send emails.

    :param template: The path where the email template is.
    :param from_addr: email address for From:
    :param to_addr: email address for To:
    :param subject: subject for the email
    :param variables: The dictonary with the variables for the template
    '''
    def __init__(self, template, from_addr, to_addr, subject, variables):
        self.template = template
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.subject = subject
        self.variables = variables
        self.__send_email()


    def __send_email(self):
        ''' Sends an email using the template '''
        with open(self.template, 'r') as f:
            self.msg = MIMEText(self.__fill_template(f.read()))
        self.subject = self.__fill_template(self.subject)
        self.msg['Subject'] = self.subject
        self.msg['From'] = self.from_addr
        self.msg['To'] = self.to_addr
        s = smtplib.SMTP('localhost')
        s.send_message(self.msg)
        s.quit()


    def __fill_template(self, text):
        text = Template(text)
        return(text.safe_substitute(self.variables))
