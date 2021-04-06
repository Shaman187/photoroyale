from django.shortcuts import render, redirect
import uuid
import boto3
from .models import Thread, Post, Comment, Image
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin


S3_BASE_URL = 'https://s3-us-east-2.amazonaws.com/'
BUCKET = 'catcollector187'

# Create your views here.


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


class ThreadCreate(LoginRequiredMixin, CreateView):
    model = Thread
    fields = ['title', 'description']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class ThreadDelete(LoginRequiredMixin, DeleteView):
    model = Thread
    success_url = '/'


class ThreadUpdate(LoginRequiredMixin, UpdateView):
    model = Thread
    fields = ['description']


def threads_index(request):
    threads = Thread.objects.all()
    return render(request, 'threads/index.html', {'threads': threads})


def thread_posts_index(request, thread_id):
    posts = Post.objects.filter(thread=thread_id)
    thread = Thread.objects.get(id=thread_id)

    contenttype_obj = ContentType.objects.get_for_model(thread)
    image = Image.objects.filter(object_id=thread.id, content_type=contenttype_obj).first()

    fullposts = []
    for post in posts:
      contenttype_obj_post = ContentType.objects.get_for_model(posts.first())
      post_image = Image.objects.filter(object_id=posts.first().id, content_type=contenttype_obj_post).first()
      fullposts.append({'post': post, 'image': post_image})

    return render(request, 'threads/posts/index.html', {'posts': fullposts, 'thread': thread, 'image': image,})


class PostCreate(LoginRequiredMixin, CreateView):
    model = Post
    fields = []

    def form_valid(self, form):
        form.instance.user = self.request.user
        print(self.kwargs['thread_id'], 'this is self.kwargs')
        form.instance.thread = Thread.objects.get(id=self.kwargs['thread_id'])
        return super().form_valid(form)


class PostDelete(LoginRequiredMixin, DeleteView):
    model = Post

    # def get_object(self, queryset = None):
    #     thread = self.kwargs['thread_id']
    #     print(thread)
    
    success_url = '/threads/'


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = []

def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = Comment.objects.filter(post=post_id)

    contenttype_obj = ContentType.objects.get_for_model(post)
    image = Image.objects.filter(object_id=post.id, content_type=contenttype_obj).first()

    return render(request, 'threads/posts/detail.html', {'post': post, 'comments': comments, 'image': image})


def signup(request):
    error_message = ''
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
        else:
            error_message = 'Invalid sign up - try again'

    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)


class CommentCreate(LoginRequiredMixin, CreateView):
  model = Comment
  fields = ['content']

  def form_valid(self, form):
    form.instance.user = self.request.user
    form.instance.post = Post.objects.get(id=self.kwargs['post_id'])
    return super().form_valid(form)


class CommentDelete(LoginRequiredMixin, DeleteView):
  model = Comment
  success_url = '/threads/'


class CommentUpdate(LoginRequiredMixin, UpdateView):
  model = Comment
  fields = ['content']

def add_image(request, object_id):
    # photo-file will be the "name" attribute on the <input type="file">
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            # build the full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            # we can assign to cat_id or cat (if you have a cat object)
            Image.objects.create(url=url, object_id=object_id)
        except:
            print('An error occurred uploading file to S3')
    return redirect('detail', object_id=object_id)
