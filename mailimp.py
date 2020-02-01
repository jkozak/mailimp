#!/usr/bin/env python3

"""MailImp - minimal mailing list

"""

import sys
import os,pwd
import subprocess
import smtplib
import email,email.utils
import shutil
import configparser
import hashlib
import gzip

def log(txt):
    sys.stderr.write(txt)
    sys.stderr.write('\n')
    syslog.syslog(txt)

def set_log(_log):
    global log
    log = _log

def chk_out(cmd):
    return subprocess.check_output(cmd).decode('utf-8').strip()

def load_config(conf_file='config.ini'):
    c = configparser.ConfigParser(allow_no_value=True)
    c.read(conf_file)
    try:
        n = c['network']
    except KeyError:
        n = {}
    return {
        'members':  set(c['members'].keys()),
        'smtphost': n.get('smtphost','localhost'),
        'domain':   n.get('domain',chk_out('dnsdomainname'))
    }


def procmail(name=None,
             domain=None,
             smtphost='localhost',
             members=[],
             text=None,
             smtp_connection=None,
             home_dir=None):

    try:
        # validate parms
        if text is None:
            text = sys.stdin.read()
        if name is None:
            name = pwd.getpwuid(os.getuid())[0] # name of mailing list
        if domain is None:
            domain = chk_out('dnsdomainname')
            if not domain:
                log("no domain specified")
                return
        if home_dir is None:
            home_dir = pwd.getpwuid(os.getuid())[5]
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

        # stash message
        hasher = hashlib.sha1()
        hasher.update(text.encode('utf-8'))
        h = hasher.hexdigest()
        with gzip.open(os.path.join(home_dir,'received','%s.gz'%(h,)),'wb') as wzf:
            wzf.write(text.encode('utf-8'))
        log("saved msg %s from %s as %s"%(msg['Message-ID'],author,h))

        # check author is a list member
        if author not in members:
            log("%s is not a member"%(author,))
            return

        # send messages out
        smtp_connection = smtp_connection or smtplib.SMTP(smtphost)
        for m in members:
            del msg['To']
            if m!=author:
                msg['Sender'] = author
                msg['To']     = m
                log("send msg %s to %s"%(msg['Message-ID'],m))
                try:
                    smtp_connection.send_message(msg)
                except:
                    e = sys.exc_info()[0]
                    log("failed: %s"%(e,))
    finally:
        if smtp_connection:
            smtp_connection.quit()

def _sanity_check(name,home_dir=None):
    if home_dir is None:
        home_dir = pwd.getpwnam(name)[5]
    # +++ this should not be called on a running system +++
    # +++  only as part of set up +++
    # +++ fail if ~name/config.ini exists +++
    # +++ check user name has a valid shell +++
    # +++ try to deliver mail +++
    pass

def make_list(name):
    try:
        # N.B. must have a valid login shell for .forward to pipe
        subprocess.check_output("useradd -rmU %s"%(name,),shell=True)
    except:
        sys.exit("failed to add list user %s"%(name,))
    home_dir = pwd.getpwnam(name)[5]
    # +++ maybe: subprocess.check_output("rm -rf %s/*"%(home_dir,))
    open(os.path.join(home_dir,'config.ini'),'w').write('''\
[members]
# put members here, one per line, no equals sign

[network]
# smtphost = mailfae
# domain   = example.org

''')
    open(os.path.join(home_dir,'.forward'),'w').write('''\
"|/usr/bin/flock %s/lockfile %s dotforward"
'''%(home_dir,__file__) )
    os.mkdir(os.path.join(home_dir,'received'))
    subprocess.check_output("chown -R %s.%s %s"%(name,name,home_dir),shell=True)

def remove_list(name):
    try:
        subprocess.check_output("userdel -rf %s"%(name,),shell=True)
    except:
        sys.exit("failed to delete list user")

if __name__=='__main__':
    import syslog
    syslog.openlog('mailimp')
    if len(sys.argv)==1:
        sys.exit("I must write some help")
    elif sys.argv[1]=='dotforward':
        uid,cwd = os.getuid(),os.getcwd()
        if pwd.getpwuid(uid)[5]!=cwd:
            log("must run in %s's home dir, not %s"%(uid,os.cwd))
        else:
            cfg = load_config()
            procmail(members  = cfg['members'],
                     smtphost = cfg['smtphost'],
                     domain   = cfg['domain'])
    elif sys.argv[1] in ['mk','make'] and len(sys.argv)==3:
        if os.getuid()!=0:
            log("must run as root")
        else:
            make_list(sys.argv[2])
    elif sys.argv[1] in ['rm','remove'] and len(sys.argv)==3:
        if os.getuid()!=0:
            log("must run as root")
        else:
            remove_list(sys.argv[2])
    else:
        sys.exit("unknown cmd: %s"%(sys.argv[1],))
