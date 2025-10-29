from django.urls import path, reverse_lazy
from userauths import views

app_name = 'userauths'

urlpatterns = [
    path("sign-up/", views.register, name="sign-up"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    
    path("password-reset/", views.reset_password_request, name="password_reset"),
    path("password-reset/security/", views.reset_password_security, name="reset_password_security"),
    path("password-reset/new/", views.set_new_password, name="set_new_password"),
]