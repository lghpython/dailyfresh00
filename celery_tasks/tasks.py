import time

from celery import Celery
from django.core.mail import send_mail
from django_redis import get_redis_connection

from dailyfresh00 import settings

app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/5')


@app.task
def send_register_active_email(to_email, username, token):
    subject = '天天生鲜欢迎信息'
    message = ''
    receiver = [to_email]
    sender = settings.EMAIL_FROM
    html_message = '<h1> {0}， 欢迎您注册成为天天生鲜用还<h1> <br>请点击下面链接激活账户<br/>' \
                   '<a href="http://127.0.0.1:8000/user/active/{1}">' \
                   'http://127.0.0.1:8000/user/active/{2}<a/>'.format(username, token, token)
    send_mail(subject, message, sender, receiver, html_message=html_message)
    # time.sleep(5)
