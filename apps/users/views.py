# coding: utf-8

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.contrib.auth.hashers import make_password


from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm
from utils.email import send_register_email


class CustomBackend(ModelBackend):
    """
    自定义登录逻辑，支持用户名或邮箱登录
    """
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class ActiveUserView(View):
    """
    激活用户并返回登录页面
    """
    def get(self, request, active_code):
        email_records = EmailVerifyRecord.objects.filter(code=active_code)
        if email_records:
            for email_record in email_records:
                email = email_record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
            return render(request, 'login.html', {})
        else:
            return render(request, 'active_fail.html', {})


class ResetView(View):
    """
    返回密码重置页面
    """
    def get(self, request, reset_code):
        email_records = EmailVerifyRecord.objects.filter(code=reset_code)
        if email_records:
            for email_record in email_records:
                email = email_record.email
                return render(request, 'password_reset.html', {"email": email})
        else:
            return render(request, 'active_fail.html', {})


class ModifyPwdView(View):
    """
    验证用户修改的新密码，并返回登录页面
    """
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email": email, "msg": "两次密码不一致"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd1)
            user.save()
            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email": email, "modify_form": modify_form})


class RegisterView(View):
    """
    用户注册
    """
    def get(self, request):
        register_form = RegisterForm()
        return render(request, 'register.html', {"register_form": register_form})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            email = request.POST.get("email")
            password = request.POST.get("password")
            if UserProfile.objects.filter(email=email):
                return render(request, "register.html", {"register_form": register_form, "msg": "该邮箱已注册"})
            user = UserProfile()
            user.username = email
            user.email = email
            user.is_active = False
            user.password = make_password(password)
            user.save()
            send_register_email(email)
            return render(request, 'login.html', {"user": {"email": email, "password": password}, "msg": "请先登录邮箱进行验证"})
        else:
            return render(request, 'register.html', {"register_form": register_form})


class LoginView(View):
    """
    用户登录
    """
    def get(self, request):
        return render(request, "login.html", {})

    def post(self, request):
        login_forms = LoginForm(request.POST)
        if login_forms.is_valid():
            user_name = request.POST.get("username", "")
            pass_word = request.POST.get("password", "")
            user = authenticate(username=user_name, password=pass_word)
            if user is not None:
                if not user.is_active:
                    return render(request, "login.html", {"msg": "用户未激活"})
                login(request, user)
                return render(request, 'index.html', {})
            else:
                return render(request, "login.html", {"msg": "用户名或密码错误"})
        else:
            return render(request, "login.html", {"login_forms": login_forms})


class ForgetPwdView(View):
    """
    忘记密码页面，发送重置密码链接到用户邮箱
    """
    def get(self, request):
        forget_form = ForgetForm()
        return render(request, 'forgetpwd.html', {"forget_form": forget_form})

    def post(self, request):
        forget_form = ForgetForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get("email", "")
            send_register_email(email, 'forget')
            return render(request, 'send_success.html')
        else:
            return render(request, 'forgetpwd.html', {"forget_form": forget_form})


# 函数的方式处理响应
def mylogin(request):
    if request.method == "POST":
        user_name = request.POST.get("username", "")
        pass_word = request.POST.get("password", "")
        user = authenticate(username=user_name, password=pass_word)
        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'index.html', {})
            else:
                return render(request, "login.html", {"msg": "该用户未激活"})
        else:
            return render(request, "login.html", {"msg": "用户名或密码错误"})
    elif request.method == "GET":
        return render(request, "login.html", {})
