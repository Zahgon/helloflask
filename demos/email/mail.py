# -*- coding: utf-8 -*-
"""A small SMTP helper (replacement for the Flask-Mail extension)."""
import smtplib
from email.message import EmailMessage
from email.utils import formataddr


class Message:
    """An email message."""

    def __init__(self, subject, recipients, body=None, html=None, sender=None):
        self.subject = subject
        self.recipients = recipients
        self.body = body
        self.html = html
        self.sender = sender


class Mail:
    """Send messages over SMTP, using the application config."""

    def __init__(self, app):
        self.config = app.state.config

    @staticmethod
    def format_sender(sender):
        if isinstance(sender, (tuple, list)):
            return formataddr(tuple(sender))
        return sender

    def build_message(self, message):
        email = EmailMessage()
        email['Subject'] = message.subject
        email['From'] = self.format_sender(message.sender or self.config['MAIL_DEFAULT_SENDER'])
        email['To'] = ', '.join(message.recipients)
        email.set_content(message.body or '')
        if message.html:
            email.add_alternative(message.html, subtype='html')
        return email

    def connect(self):
        config = self.config
        if config.get('MAIL_USE_SSL'):
            return smtplib.SMTP_SSL(config['MAIL_SERVER'], config['MAIL_PORT'])
        server = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'])
        if config.get('MAIL_USE_TLS'):
            server.starttls()
        return server

    def send(self, message):
        with self.connect() as server:
            if self.config.get('MAIL_USERNAME'):
                server.login(self.config['MAIL_USERNAME'], self.config['MAIL_PASSWORD'])
            server.send_message(self.build_message(message))
