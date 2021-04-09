from django.shortcuts import render, redirect
from .models import Thread, Post, Comment, Image
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import ThreadForm, PostForm
from django.urls import reverse
from PIL import Image as pilImage
from io import BytesIO
import uuid
import boto3


S3_BASE_URL = 'https://s3-us-east-2.amazonaws.com/'
BUCKET = 'catcollector187'

# Create your views here.


def home(request):
    return redirect('/threads/')


def about(request):
    return render(request, 'about.html')

def thread_render(request):
    return render(request, 'threads/thread_form.html')

def post_render(request, thread_id):
    return render(request, 'threads/posts/post_form.html', {'thread_id': thread_id})

@login_required
def ThreadCreate(request):
    # create the ModelForm using the data in request.POST
    form = ThreadForm(request.POST)
    # validate the form
    if form.is_valid():
        if 'image' in request.FILES.get('image', None).content_type:
            new_thread = form.save(commit=False)
            new_thread.user = request.user
            new_thread.save()

            check_try = add_photo(request.FILES.get('image', None), new_thread.id, ContentType.objects.get_for_model(new_thread))

            if check_try: 
                return redirect(f'/threads/{new_thread.id}')
            else:
                return render(request, 'errors/image_error.html', {'path': 'thread_render', 'id':None, 'error': 'We cannot process this image :('})
        else:
            return render(request, 'errors/image_error.html', {'path': 'thread_render', 'id':None, 'error': 'File must be an image type'})
    return redirect('/threads/')

def add_photo(photo_file, object_id, object_type):

    if photo_file:
        s3 = boto3.client('s3')
        # need a unique "key" for S3 / needs image file extension too
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        # just in case something goes wrong
        try:
            size = (1024, 1024)
            im = pilImage.open(photo_file)
            im.thumbnail(size)
            buffer = BytesIO()
            im.save(buffer, 'PNG')
            buffer.seek(0)

            s3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body=buffer,
                ContentType='image/png',
            )
            # build the full url string
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            Image.objects.create(url=url, content_type=object_type, object_id=object_id)
        except:
            if str(object_type) == 'main_app | post':
                Post.objects.get(id=object_id).delete()
            else:
                Thread.objects.get(id=object_id).delete()
            return False
    return True

class ThreadDelete(LoginRequiredMixin, DeleteView):
    model = Thread
    success_url = '/'


class ThreadUpdate(LoginRequiredMixin, UpdateView):
    model = Thread
    fields = ['description']


def threads_index(request):
    threads = Thread.objects.all()

    fullthreads = []
    for thread in threads:
      contenttype_obj_thread = ContentType.objects.get_for_model(thread)
      thread_image = Image.objects.filter(object_id=thread.id, content_type=contenttype_obj_thread).first()
      fullthreads.append({'thread': thread, 'image': thread_image})

    return render(request, 'threads/index.html', {'threads': fullthreads})


def thread_posts_index(request, thread_id):
    posts = Post.objects.filter(thread=thread_id)
    thread = Thread.objects.get(id=thread_id)

    contenttype_obj = ContentType.objects.get_for_model(thread)
    image = Image.objects.filter(object_id=thread.id, content_type=contenttype_obj).first()

    fullposts = []
    for post in posts:
      contenttype_obj_post = ContentType.objects.get_for_model(post)
      post_image = Image.objects.filter(object_id=post.id, content_type=contenttype_obj_post).first()
      fullposts.append({'post': post, 'image': post_image})

    return render(request, 'threads/posts/index.html', {'posts': fullposts, 'thread': thread, 'image': image,})

@login_required
def post_create(request, thread_id):
    # create the ModelForm using the data in request.POST
    form = PostForm(request.POST)
    # validate the form
    if form.is_valid():
        if 'image' in request.FILES.get('image', None).content_type:
            new_post = form.save(commit=False)
            new_post.user = request.user
            new_post.thread = Thread.objects.get(id=thread_id)
            new_post.save()
            check_try = add_photo(request.FILES.get('image', None), new_post.id, ContentType.objects.get_for_model(new_post))
            if check_try:
                return redirect(f'/threads/posts/{new_post.id}')
            else:
                return render(request, 'errors/image_error.html', {'path': 'post_render', 'id':thread_id, 'error': 'We cannot process this image :('})
        else:
            return render(request, 'errors/image_error.html', {'path': 'post_render', 'id':thread_id, 'error': 'File must be an image type'})
    return redirect('/threads/')

class PostDelete(LoginRequiredMixin, DeleteView):
    model = Post

    def get_success_url(self):
        return reverse('thread_posts_index', kwargs={'thread_id': self.object.thread.id}) 


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['description']

def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = Comment.objects.filter(post=post_id)
    thread = Thread.objects.get(id=post.thread.id)
    contenttype_obj = ContentType.objects.get_for_model(post)
    image = Image.objects.filter(object_id=post.id, content_type=contenttype_obj).first()

    return render(request, 'threads/posts/detail.html', {'post': post, 'comments': comments, 'image': image, 'thread': thread})


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
  def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.post.id}) 


class CommentUpdate(LoginRequiredMixin, UpdateView):
  model = Comment
  fields = ['content']


