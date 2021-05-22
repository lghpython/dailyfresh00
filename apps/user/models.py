from django.contrib.auth.models import AbstractUser
from django.db import models

from db.base_model import BaseModel


class User(AbstractUser, BaseModel):
    """ 用户数据模型类 """
    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

class AddressManager()

class Address(BaseModel):
    user = models.ForeignKey('User', verbose_name='所属用户', on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    address = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='手机号码')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    class Meta:
        db_table = 'df_address'
        verbose_name = "地址"
        verbose_name_plural = verbose_name



        return