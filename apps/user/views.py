import re

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail

from celery_tasks.tasks import send_register_active_email
from dailyfresh00 import settings
from user.models import User, Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': "注册信息不能为空"})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意用户协议'})

        try:
            user = User.objects.get(username='username')
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已注册'})

        user = User.objects.create_user(username, password, email)
        user.is_active = 0
        user.save()

        ## 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()

        # subject = '天天生鲜欢迎信息'
        # message = ''
        # receiver = [email]
        # sender = settings.EMAIL_FROM
        # html_message = '<h1> {0}， 欢迎您注册成为天天生鲜用还<h1> <br>请点击下面链接激活账户<br/>' \
        #                '<a href="http://127.0.0.1:8000/user/active/{1}">' \
        #                'http://127.0.0.1:8000/user/active/{2}<a/>'.format(username, token, token)
        # send_mail(subject, message, sender, receiver, html_message=html_message)
        send_register_active_email.delay(email, username, token)
        # 返回应答, 跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    """ 激活用户账户 """

    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3360)
        try:

            info = serializer.loads(token)
            uid = info['confirm']

            user = User.objects.get(id=uid)
            user.active = 1
            user.save()

            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse("激活链接已失效")


class LoginView(View):
    def get(self, request):
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''

        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        if not all([username, password]):
            return render('login.html', {"errmsg": '登录数据不完整'})

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)

                next_url = reverse('goods:index')

                response = redirect(next_url)

                remember = request.GET.get('remember')

                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                return response
            else:
                return render(request, 'login.html', {'errmsg': '账户未激活'})
        else:
            return render(request, 'login.html', {'errmsh': '用户名或密码错误'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('user:login')


# class UserInfoView(LoginRequiredMixin, View):
class UserInfoView( View):
    def get(self, request):
        # 获取登录用户基本信息, 用户名， 联系电话， 地址
        user = request.user
        address = Address.Objects.get_default_address(user)

        # 获取最近浏览记录 （图片、商品名称、价格 、 单价）
        goods_li = []

        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li
        }

        return render(request, "user_center_info.html", context)


class UserOrderView(View):
    def get(self, request):
        order_page = []
        return render(request, "user_center_order.html", order_page)


class AddressView(View):
    def get(self, request):
        return render(request,"user_center_site.html")

    def post(self, request):
        pass
