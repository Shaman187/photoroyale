from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('accounts/signup/', views.signup, name='signup'),
    path('threads/', views.threads_index, name='index'),
    path('threads/new/', views.ThreadCreate.as_view(), name='thread_create'),
    path('threads/<int:pk>/update/', views.ThreadUpdate.as_view(), name='thread_update'),
    path('threads/<int:thread_id>/', views.thread_posts_index, name='thread_posts_index'),
    path('threads/<int:pk>/delete/', views.ThreadDelete.as_view(), name='thread_delete'),
    path('threads/<int:thread_id>/posts/new/', views.PostCreate.as_view(), name='post_create'),
    path('threads/posts/<int:pk>/delete/', views.PostDelete.as_view(), name='post_delete'),
    path('threads/posts/<int:pk>/update/', views.PostUpdate.as_view(), name='post_update'),
    path('threads/posts/<int:post_id>/', views.post_detail, name='post_detail'),

]