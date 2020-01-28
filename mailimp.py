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

def set_log(_log):
    log = log_

def procmail(name=None,
             domain=None,
             smtphost='localhost',
             members=[],
             text=None,
             smtp_connection=None):

    try:
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
        source = "%s mailing list <%s@%s>"%(name,name,domain)
        if auth_nv[0]:
            source = "%s via %s"%(auth_nv[0],source)
        msg['Reply-To'] = msg['From'] = source

        # check author is a list member
        if author not in members:
            log("%s is not a member"%(author,))
            # +++ stash message somewhere +++
            return

        # send messages out
        smtp_connection = smtp_connection or smtplib.SMTP(smtphost)
        for m in members:
            del msg['To']
            if m!=author:
                msg['Sender'] = author
                msg['To']     = m
                log("send msg %s to %s"%(msg['Message-Id'],m))
                try:
                    smtp_connection.send_message(msg)
                except:
                    e = sys.exc_info()[0]
                    log("failed: %s"%(e,))
    finally:
        if smtp_connection:
            smtp_connection.quit()

def new_list(name):
    subprocess.check_output("adduser --system --group %s"%(name,))
    # +++ create /home/{name}/rcve.py +++
    # +++ create .forward file +++
    #   "|/usr/bin/flock /home/{name}/lockfile /home/{name}/rcve.py"

def del_list(name):
    # +++ rm -rf /home/{name} +++
    pass
