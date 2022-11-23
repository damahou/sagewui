# -*- coding: utf-8 -*-

# py3: twisted.mail is not ported to py3 (20160712)
try:
    from smtpsend import send_mail
except ImportError:
    def send_mail(*args, **kwargs):
        print("send mail disabled.")
