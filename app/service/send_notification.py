# -*- coding: utf-8 -*-

import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app import log, config

LOG = log.get_logger()


def send_email(to_email, subject, content_html):
    message = MIMEMultipart("mixed")
    message["Subject"] = subject
    message["From"] = config.EMAIL["SENDER"]
    message["To"] = to_email

    # write the HTML part
    part = MIMEText(content_html, "html")
    message.attach(part)

    with smtplib.SMTP(config.EMAIL["SMTP_SERVER"], config.EMAIL["SMTP_PORT"]) as server:
        if config.EMAIL["SMTP_TLS"]:
            LOG.info("SMTP server initiating a secure connection with TLS")
            server.starttls()
        LOG.info("SMTP server {0}:{1} started".format(config.EMAIL["SMTP_SERVER"], config.EMAIL["SMTP_PORT"]))
        server.login(config.EMAIL["SMTP_USERNAME"], config.EMAIL["SMTP_PASSWORD"])
        LOG.info("SMTP server logged in with user {0}".format(config.EMAIL["SMTP_USERNAME"]))
        server.sendmail(config.EMAIL["SENDER"], to_email, message.as_bytes())
        LOG.info("SMTP server sent email message")
