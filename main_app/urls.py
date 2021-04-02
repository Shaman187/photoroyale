from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('accounts/signup/', views.signup, name='signup'),
    path('threads/', views.threads_index, name='index'),
    path('threads/create', views.ThreadCreate.as_view(), name='thread_create'),
]