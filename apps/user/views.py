import re

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.core.mail import send_mail
from django_redis import get_redis_connection

from celery_tasks.tasks import send_register_active_email
from dailyfresh00 import settings
from goods.models import GoodsSKU
from user.models import User, Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired

from utils.mixin import LoginRequiredMixin


class RegisterView(View):
    ''' 注册页面 '''

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
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user:
            return render(request, 'register.html', {'errmsg': '用户名已注册'})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        ## 发送激活邮件，包含激活链接: http://127.0.0.1:8000/user/active/3
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()
        print(info, token)

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
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:

            info = serializer.loads(token)
            uid = info['confirm']
            print(uid)
            user = User.objects.get(id=uid)
            user.is_active = 1
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
        print([username, password, user])
        if user is not None:
            if user.is_active:
                login(request, user)

                next_url = request.GET.get('next', reverse('goods:index'))
                print(next_url)
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
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('user:login')


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取登录用户基本信息, 用户名， 联系电话， 地址
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取最近浏览记录 （图片、商品名称、价格 、 单价）
        conn = get_redis_connection('default')
        history_key = "history_%d"%user.id
        sku_ids = conn.lrange(history_key, 0, 4)
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        context = {
            'page': 'user',
            'address': address,
            'goods_li': goods_li
        }

        return render(request, "user_center_info.html", context)


class UserOrderView(LoginRequiredMixin, View):
    def get(self, request):
        order_page = []
        return render(request, "user_center_order.html", order_page)


class AddressView(View):
    # class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)
        return render(request, "user_center_site.html", {'page': 'address', 'address': address})

    def post(self, request):
        # 提交 新地址
        receiver = request.POST.get('receiver')
        addr = request.POST.get('address')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        print([receiver, phone, zip_code, addr])
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '地址信息不完整'})

        if not re.match(r'^1[3|4|5|7|8|][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg': '手机格式不正确'})

        user = request.user

        # 设置默认地址
        address = Address.objects.get_default_address(user)
        is_default = False if address else True

        Address.objects.create(user=user,
                               receiver=receiver,
                               address=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default
                               )

        return redirect(reverse('user:address'))
