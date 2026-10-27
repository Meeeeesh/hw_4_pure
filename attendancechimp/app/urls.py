from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # HW2
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum'),
    path('', views.index, name='home'),
    path('index.html', views.index, name='index_html'),
    path('new', views.new_user_form, name='new'),
    path('createUser', views.createUser, name='createUser'),
    path('login', auth_views.LoginView.as_view(), name='login'),
]