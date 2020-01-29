#!/usr/bin/env python3

"""MailImp - minimal mailing list

"""

import sys
import os,pwd
import subprocess
import smtplib
import email,email.utils
import syslog
import shutil

syslog.openlog('mailimp')

def log(txt):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    syslog.syslog(txt)

def set_log(_log):
    global log
    log = _log

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
    try:
        subprocess.check_output("useradd -rmU -s /bin/false %s"%(name,))
    except:
        sys.exit("failed to add list user")
    home_dir = pwd.getpwnam(name)[5]
    # +++ maybe: subprocess.check_output("rm -rf %s/*"%(home_dir,))
    open(os.path.join(home_dir,'main.py','w')).write('''\
#!/usr/bin/env python3

MEMBERS = []

if __name__=='__main__':
    import mailimp
    mailimp.procmail(members=MEMBERS)

''')
    open(os.path.join(home_dir,'.forward','w')).write('''\
"|/usr/bin/flock %s/lockfile %s/main.py"
'''%(home_dir,home_dir) )
    subprocess.check_output("chown -R %s.%s %s"%(name,name,home_dir))

def del_list(name):
    try:
        subprocess.check_output("userdel -rf %s"%(name,))
    except:
        sys.exit("failed to delete list user")
