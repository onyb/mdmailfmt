#!/usr/bin/env python
# -*- coding: utf-8 -*-

from contextlib import contextmanager
import csv
import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from os.path import basename
import time

import markdown



DEBUG = False
DEBUG_ITER_LIMIT = 10


def get_defaults():
    class Defaults:
        SMTP_SERVER_HOST = 'smtp.gmail.com'
        SMTP_SERVER_PORT = 587
    return Defaults()


def get_md_message(markdown_body_filename):
    with open(markdown_body_filename) as f:
        md_message = f.read()
    return md_message


def get_addr_and_values(csv_values_filename, delimiter, quotechar):
    with open(csv_values_filename, newline='') as f:
        reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
        keys = next(reader)
        return [
            (
                values[0],
                {
                    k: v
                    for k, v in zip(keys[1:], values[1:])
                }
            )
            for values in reader
        ]


def email_obj_of_md(from_address, to_address, subject, md_message):
    email_obj = MIMEMultipart('alternative')
    email_obj['To'] = to_address
    email_obj['From'] = from_address
    email_obj['Subject'] = subject
    part1, part2 = parts_of_md(md_message)
    email_obj.attach(part1)
    email_obj.attach(part2)
    return email_obj


def parts_of_md(md_message):
    return (
        MIMEText(md_message, 'text'),
        MIMEText(markdown.markdown(md_message), 'html')
    )


def attach_filename(email_obj, attachment_filename):
    with open(attachment_filename, 'rb') as f:
        attachment = f.read()
    attachment_mimeapp = MIMEApplication(attachment)
    attachment_mimeapp.add_header(
        'Content-Disposition', 'attachment',
        filename=basename(attachment_filename))
    email_obj.attach(attachment_mimeapp)
    return email_obj


def render_messages(msg, values):
    return msg.format(**values)


def setup_smtp_server(smtp_server_host, smtp_server_port, smtp_login,
                      smtp_password):
    smtp_server = smtplib.SMTP(smtp_server_host, smtp_server_port)
    smtp_server.starttls()
    smtp_server.ehlo()
    smtp_server.login(smtp_login, smtp_password)
    return smtp_server


def print_debug(var, desc, limit=None):
    v = var if limit is None else var[:limit]
    print('\n{}: \n{}\n--------------------------------------------------------'
          .format(desc, v))


@contextmanager
def running_smtp_connection(smtp_server_host,
                            smtp_server_port,
                            smtp_login,
                            smtp_password):
    smtp_server = setup_smtp_server(smtp_server_host,
                                    smtp_server_port,
                                    smtp_login,
                                    smtp_password)
    try:
        yield smtp_server
    finally:
        smtp_server.quit()


# [XXX] - Check if this works with a lot of TO's
# [XXX] - Add try/excepts around each call to give some feedback. Print stack
# trace if debug.
def main(args):
    md_message = get_md_message(args.markdown_body_filename)
    if DEBUG:
        print_debug(md_message, 'Markdown message')
    email_addresses_and_values = get_addr_and_values(args.csv_values_filename,
                                                     args.csv_delimiter,
                                                     args.csv_quotechar)
    if DEBUG:
        print_debug(email_addresses_and_values, 'Email addresses and values',
                    limit=DEBUG_ITER_LIMIT)
    recipient_email_addresses = [ev[0] for ev in email_addresses_and_values]
    if DEBUG:
        print_debug(recipient_email_addresses, 'Recipient email addresses',
                    limit=DEBUG_ITER_LIMIT)
    values = [ev[1] for ev in email_addresses_and_values]
    if DEBUG:
        print_debug(values, 'Values', limit=DEBUG_ITER_LIMIT)
    md_bodies = [render_messages(md_message, value) for value in values]
    if DEBUG:
        print_debug(md_bodies, 'Markdown bodies', limit=DEBUG_ITER_LIMIT)

    batch_length = args.paging
    recipients_and_bodies = zip(
        recipient_email_addresses,
        md_bodies
    )
    while batch_length == args.paging:
        with running_smtp_connection(args.smtp_server_host,
                                     args.smtp_server_port,
                                     args.smtp_login,
                                     args.smtp_password) as smtp_server:
            batch_length = 0
            for i, (recipient_email_address, md_body) in enumerate(
                    recipients_and_bodies
            ):
                smtp_server.ehlo()
                email_obj = email_obj_of_md(args.from_address,
                                            recipient_email_address,
                                            args.subject, md_body)
                for attachment in args.attachments:
                    email_obj = attach_filename(email_obj, attachment)
                smtp_recipients = [recipient_email_address] + args.bcc_addresses
                smtp_server.sendmail(args.from_address, smtp_recipients,
                                     email_obj.as_string())
                sys.stdout.write(
                    '{} - Email sent to {}\n'.format(
                        datetime.datetime.now().isoformat(),
                        recipient_email_address
                    )
                )
                if i + 1 == args.paging:
                    break
            batch_length = i + 1
        time.sleep(args.pause_in_seconds)


if __name__ == '__main__':
    import argparse
    import os
    import sys

    defaults = get_defaults()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--debug-iter-limit', type=int)
    parser.add_argument('--smtp-server-host', default=defaults.SMTP_SERVER_HOST)
    parser.add_argument('--smtp-server-port', default=defaults.SMTP_SERVER_PORT,
                        type=int)
    parser.add_argument('--smtp-login', default=os.getenv('SMTP_LOGIN'))
    parser.add_argument('--smtp-password', default=os.getenv('SMTP_PASSWORD'))
    parser.add_argument('--from',
                        required=True,
                        help="From email address (this should be yours).",
                        dest='from_address')
    parser.add_argument('--bcc',
                        type=(lambda s: s.split(',')),
                        help="BCC email addresses (comma-separated list input).",
                        dest='bcc_addresses',
                        default=[])
    parser.add_argument('--subject',
                        required=True,
                        help='The email subject.')
    parser.add_argument('--markdown-body',
                        required=True,
                        help='The email body contents markdown template file.',
                        dest='markdown_body_filename')
    parser.add_argument('--attachments',
                        type=(lambda s: s.split(',')),
                        help="Attachment filenames (comma-separated list input).",
                        dest='attachments',
                        default=[])
    parser.add_argument('--csv-values',
                        required=True,
                        help=(
                            'The csv file containing email addresses and '
                            'corresponding body template values. This MUST '
                            'a first row with key names.'
                        ),
                        dest='csv_values_filename')
    parser.add_argument('--paging',
                        required=True,
                        type=int,
                        help=(
                            'Restart the SMTP connection every that many '
                            'entries in the CSV file'
                            '(goes with the "pause-in-seconds" argument).'
                        ),
                        dest='paging')
    parser.add_argument('--pause-in-seconds',
                        required=True,
                        type=int,
                        help=(
                            'Duration of the pause between each SMTP connection'
                            '(goes with the "paging" argument).'
                        ),
                        dest='pause_in_seconds')
                        
    parser.add_argument('--csv-delimiter', default=',')
    parser.add_argument('--csv-quotechar', default='"')

    _args = parser.parse_args()

    DEBUG = _args.debug  # [XXX] - Do smght

    if not _args.smtp_login or not _args.smtp_password:
        sys.stderr.write('Failure: no login or no password.\n')
        sys.stdout.write(
            '[FAILURE] You have to enter your SMTP login and password!\n'
        )
        sys.exit(1)

    main(_args)
