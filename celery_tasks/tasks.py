import os.path
import time

from celery import Celery
from django.core.mail import send_mail
from django.template import loader, RequestContext
from django_redis import get_redis_connection
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh00.settings")
django.setup()
from dailyfresh00 import settings
from goods.models import GoodsType, IndexGoodsBanner, IndexPromotionBanner, IndexGoodsTypeBanner

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


@app.task
def generate_static_index_html():
    # 获取商品类型
    types = GoodsType.objects.all()
    # 获取商品轮播数据
    index_goods_banner = IndexGoodsBanner.objects.all().order_by('index')
    # 获取商品促销活动数据
    index_promotion_banner = IndexPromotionBanner.objects.all().order_by('index')

    # 获取商品分类展示数据
    for type in types:
        title_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=0).order_by('index')
        image_banners = IndexGoodsTypeBanner.objects.filter(type=type, display_type=1).order_by('index')
        type.title_banners = title_banners
        type.image_banners = image_banners
    print('----------------')
    # 上下文整合数据
    context = {'index_goods_banner': index_goods_banner,
               'index_promotion_banner': index_promotion_banner,
               'types': types,
               }

    # 使用模板
    temp = loader.get_template('static_index.html')
    # # 整理上下文
    # context = RequestContext(request, context)
    # 模板渲染
    static_index_html = temp.render(context)
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path,'w') as f:
        f.write(static_index_html)
