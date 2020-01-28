#!/usr/bin/env python3

import sys
import os,pwd
import subprocess
import smtplib
from email.message import EmailMessage

def log(txt):
    sys.stderr.write(txt)
    sys.stderr.write('\n')

def procmail(name=None,
             domain=None,
             smtphost='localhost',
             members=[],
             body=None):

    # validate parms
    if body is None:
        body = sys.stdin.read()
    if name is None:
        name = pwd.getpwuid(os.getuid())[0] # name of mailing list
    if domain is None:
        domain = subprocess.check_output('dnsdomainname').strip()
    if smtphost is None:
        smtphost = 'localhost'

    # build a mail object
    msg = EmailMessage()
    msg.set_content(body)
    author = msg['From']

    # check author is a member
    if author not in members:
        log(f"{author} is not a member")
        # +++ stash message somewhere +++
        return

    # send messages out
    msg['From'] = f"{name} mailing list <{name}@{domain}>"
    s           = smtplib.SMTP(smtphost)
    for m in members:
        if m!=author:
            msg['Sender'] = author
            msg['To']     = m
            s.send_message(msg)
            log(f"sent msg {msg['Message-Id']} to {m}")
    s.quit()
