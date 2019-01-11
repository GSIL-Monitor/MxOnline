# coding: utf-8
import random
import string

from django.core.mail import send_mail
from users.models import EmailVerifyRecord
from settings import EMAIL_FROM


def send_register_email(email, send_type="register"):
    email_record = EmailVerifyRecord()
    code = random_code(16)
    email_record.code = code
    email_record.send_type = send_type
    email_record.email = email
    email_record.save()

    send_title = ""
    send_body = ""

    if send_type == "register":
        send_title = "慕雪在线注册激活链接"
        send_body = "请点击如下链接激活你的账号：http://127.0.0.1:8000/active/{}".format(code)
        send_status = send_mail(send_title, send_body, EMAIL_FROM, [email])
        if send_status:
            pass


def random_code(length=16):
    return ''.join(random.sample(string.ascii_letters + string.digits, length))