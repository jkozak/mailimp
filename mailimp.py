#!/usr/bin/env python3

import sys
import os,pwd
import subprocess
import smtplib
import email,email.utils
import syslog

syslog.openlog('mailimp')

def log(txt):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    syslog.syslog(txt)

def procmail(name=None,
             domain=None,
             smtphost='localhost',
             members=[],
             dry_run=False,
             text=None):

    # validate parms
    if text is None:
        text = sys.stdin.read()
    if name is None:
        name = pwd.getpwuid(os.getuid())[0] # name of mailing list
    if domain is None:
        domain = subprocess.check_output('dnsdomainname',encoding='utf-8').strip()
        if not domain:
            log("no domain specified")
            return
    if smtphost is None:
        smtphost = 'localhost'
    members = [email.utils.parseaddr(m)[1] for m in members]

    # build a mail object suitable for sending on
    msg     = email.message_from_string(text)
    auth_nv = email.utils.parseaddr(msg['From'])
    author  = auth_nv[1]
    del msg['To']
    del msg['Sender']
    del msg['From']
    del msg['Cc']
    del msg['Bcc']
    del msg['Reply-To']
    msg['Reply-To'] = msg['From'] = "%s via %s mailing list <%s@%s>"%(auth_nv[0],name,name,domain)

    # check author is a list member
    if author not in members:
        log("%s is not a member"%(author,))
        # +++ stash message somewhere +++
        return

    # send messages out
    s = smtplib.SMTP(smtphost)
    for m in members:
        del msg['To']
        if m!=author:
            msg['Sender'] = author
            msg['To']     = m
            if dry_run:
                log(("--------------------------------------------\n\n"
                     "\n"
                     "--------------------------------------------")%(msg.as_string(),) )
            else:
                s.send_message(msg)
            log("sent msg %s to %s"%(msg['Message-Id'],m))
    s.quit()
