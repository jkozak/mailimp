import mailimp

import pytest
import email,email.utils

@pytest.fixture
def smtp_connection():
    class SmtpConn:
        def __init__(self):
            self.msgs = []
            self.is_open = True
        def send_message(self,msg):
            self.msgs.append(msg)
        def quit(self):
            self.is_open = False
    return SmtpConn()

@pytest.fixture
def log():
    class Log:
        def __init__(self):
            self.msgs = []
        def __call__(self,msg):
            self.msgs.append(msg)
    return Log()

def test_it_works_the_way_I_think_it_does_1(smtp_connection):
    assert len(smtp_connection.msgs)==0
    assert smtp_connection.is_open
    smtp_connection.send_message("text")
    assert len(smtp_connection.msgs)==1
    assert smtp_connection.is_open
    smtp_connection.quit()
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open

def test_it_works_the_way_I_think_it_does_2(smtp_connection):
    assert len(smtp_connection.msgs)==0

EMAIL_TEXT = '''\
From: z@y.co
Message-ID: <abcdef>
To: imptest@i.co

here is the news
'''

def test_ignore_non_member(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==0
    assert not smtp_connection.is_open

def test_send_one(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open

EMAIL_TEXT_FANCY = '''\
From: Mr Z <z@y.co>
Message-ID: <abcdef>
To: ImpTest <imptest@i.co>

here is the news
'''

def test_send_fancy_email_address(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_FANCY,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open

def test_send_two(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','b@c.co','z@y.co'],
                     text=EMAIL_TEXT,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==2
    assert not smtp_connection.is_open

EMAIL_TEXT_MANY_HEADERS = '''\
From: z@y.co
Message-ID: <abcdef>
To: imptest@i.co,test@i.co
Cc: j@k.co,k@l.co
Bcc: l@m.co

here is the news
'''

def test_sent_headers(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_MANY_HEADERS,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open
    msg = smtp_connection.msgs[0]
    assert not msg['To']
    assert email.utils.parseaddr(msg['From'])[0]=='imptest mailing list'
    assert email.utils.parseaddr(msg['From'])[1]=='imptest@i.co'
    assert email.utils.parseaddr(msg['Reply-To'])[1]=='imptest@i.co'
    assert not msg['Cc']
    assert not msg['Bcc']
    assert email.utils.parseaddr(msg['Sender'])[1]=='z@y.co'

EMAIL_TEXT_MANY_HEADERS_FANCY = '''\
From: Mr Z. <z@y.co>
Message-ID: <abcdef>
To: imptest@i.co,test@i.co
Cc: j@k.co,k@l.co
Bcc: l@m.co

here is the news
'''

def test_sent_headers_fancy(smtp_connection,log):
    mailimp.procmail(name='imptest',
                     domain='i.co',
                     smtphost='localhost',
                     members=['a@b.co','z@y.co'],
                     text=EMAIL_TEXT_MANY_HEADERS_FANCY,
                     smtp_connection=smtp_connection)
    assert len(smtp_connection.msgs)==1
    assert not smtp_connection.is_open
    msg = smtp_connection.msgs[0]
    assert not msg['To']
    assert email.utils.parseaddr(msg['From'])[0]=='Mr Z. via imptest mailing list'
    assert email.utils.parseaddr(msg['From'])[1]=='imptest@i.co'
    assert email.utils.parseaddr(msg['Reply-To'])[1]=='imptest@i.co'
    assert not msg['Cc']
    assert not msg['Bcc']
    assert email.utils.parseaddr(msg['Sender'])[1]=='z@y.co'
