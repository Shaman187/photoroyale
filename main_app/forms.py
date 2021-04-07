from django.forms import ModelForm
from .models import Post, Thread

class ThreadForm(ModelForm):
  class Meta:
    model = Thread
    fields = ['title', 'description']

class PostForm(ModelForm):
  class Meta:
    model = Post
    fields = ['description']