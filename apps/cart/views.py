from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View


class CartInfoView(LoginRequiredMixin, View):
    def get(self,request):
        pass

    def post(self,request):
        pass