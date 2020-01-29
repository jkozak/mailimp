import mailimp

import pytest
import email,email.utils
import copy

@pytest.fixture
def smtp_connection():
    class SmtpConn:
        def __init__(self):
            self.msgs = []
            self.is_open = True
        def send_message(self,msg):
            self.msgs.append(copy.deepcopy(msg))
        def quit(self):
            self.is_open = False
    return SmtpConn()

class Log:
    def __init__(self):
        self.msgs = []
    def __call__(self,msg):
        self.msgs.append(msg)

log = None

@pytest.fixture(autouse=True)
def log():
    global log
    log = Log()
    mailimp.set_log(log)

def test_it_works_the_way_I_think_it_does_1(smtp_connection):
    assert len(log.msgs)==0
    assert len(smtp_connection.msgs)==0
    assert smtp_connection.is_open
    smtp_connection.send_message("text")
    assert len(smtp_connection.msgs)==1
    mailimp.log("test text")
    assert log.msgs==["test text"]
    assert smtp_connection.is_open
    smtp_connection.quit()
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open

def test_it_works_the_way_I_think_it_does_2(smtp_connection):
    assert len(smtp_connection.msgs)==0,"get a new connection each time"
    assert len(log.msgs)==0,"get a new log object each time"

EMAIL_TEXT = '''\
From: z@y.co
Message-ID: <abcdef>
To: imptest@i.co

here is the news
'''

def test_ignore_non_member(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==0
    assert not smtp_connection.is_open
    assert len(log.msgs)==1
    assert log.msgs[0]=="z@y.co is not a member"

def test_send_one(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open
    assert len(log.msgs)==1
    assert log.msgs[0]=="send msg <abcdef> to a@b.co"

def test_send_one_crlf(smtp_connection):
    email_text = EMAIL_TEXT.replace('\n','\r\n')
    assert EMAIL_TEXT!=email_text
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=email_text,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert smtp_connection.msgs[0]['To']=='a@b.co'
    assert not smtp_connection.is_open
    assert len(log.msgs)==1
    assert log.msgs[0]=="send msg <abcdef> to a@b.co"

EMAIL_TEXT_FANCY = '''\
From: Mr Z <z@y.co>
Message-ID: <abcdef>
To: ImpTest <imptest@i.co>

here is the news
'''

def test_send_fancy_email_address(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_FANCY,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert smtp_connection.msgs[0]['To']=='a@b.co'
    assert not smtp_connection.is_open
    assert len(log.msgs)==1
    assert log.msgs[0]=="send msg <abcdef> to a@b.co"

def test_send_two(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','b@c.co','z@y.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==2
    assert smtp_connection.msgs[0]['To']=='a@b.co'
    assert smtp_connection.msgs[1]['To']=='b@c.co'
    assert not smtp_connection.is_open
    assert len(log.msgs)==2

EMAIL_TEXT_MANY_HEADERS = '''\
From: z@y.co
Message-ID: <abcdef>
To: imptest@i.co,test@i.co
Cc: j@k.co,k@l.co
Bcc: l@m.co

here is the news
'''

def test_sent_headers(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_MANY_HEADERS,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open
    msg = smtp_connection.msgs[0]
    assert msg['To']=='a@b.co'
    assert email.utils.parseaddr(msg['From'])[0]=='imptest mailing list'
    assert email.utils.parseaddr(msg['From'])[1]=='imptest@i.co'
    assert email.utils.parseaddr(msg['Reply-To'])[1]=='imptest@i.co'
    assert not msg['Cc']
    assert not msg['Bcc']
    assert email.utils.parseaddr(msg['Sender'])[1]=='z@y.co'
    assert len(log.msgs)==1
    assert log.msgs[0]=="send msg <abcdef> to a@b.co"

EMAIL_TEXT_MANY_HEADERS_FANCY = '''\
From: Mr Z. <z@y.co>
Message-ID: <abcdef>
To: imptest@i.co,test@i.co
Cc: j@k.co,k@l.co
Bcc: l@m.co

here is the news
'''

def test_sent_headers_fancy(smtp_connection):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_MANY_HEADERS_FANCY,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open
    msg = smtp_connection.msgs[0]
    assert msg['To']=='a@b.co'
    assert email.utils.parseaddr(msg['From'])[0]=='Mr Z. via imptest mailing list'
    assert email.utils.parseaddr(msg['From'])[1]=='imptest@i.co'
    assert email.utils.parseaddr(msg['Reply-To'])[1]=='imptest@i.co'
    assert not msg['Cc']
    assert not msg['Bcc']
    assert email.utils.parseaddr(msg['Sender'])[1]=='z@y.co'
    assert msg['Message-ID']=='<abcdef>'
    assert len(log.msgs)==1
    assert log.msgs[0]=="send msg <abcdef> to a@b.co"
