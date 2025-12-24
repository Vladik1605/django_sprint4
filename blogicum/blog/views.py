from django.shortcuts import render, get_object_or_404, get_list_or_404
from .models import Category, Post
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm, RegistrationForm
from django.contrib.auth import get_user_model
from django.http import Http404
from django.urls import reverse
from django.views.decorators.http import require_http_methods


# Create your views here.
def index(request):
    template = 'blog/index.html'

    posts_qs = (Post.objects
               .select_related('location', 'category', 'author')
               .filter(Q(pub_date__lte=timezone.now())
                       & Q(is_published__exact=True)
                       & Q(category__is_published__exact=True))
               .order_by('-pub_date'))
    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'post_list': page_obj.object_list, 'page_obj': page_obj}
    return render(request, template, context=context)


def post_detail(request, id):
    template = 'blog/detail.html'
    User = get_user_model()
    try:
        post = Post.objects.select_related('location', 'category', 'author').get(pk=id)
    except Post.DoesNotExist:
        raise Http404

    public = (post.pub_date <= timezone.now() and post.is_published and post.category and post.category.is_published)
    if not public:
        # allow author to see his own unpublished/postponed posts
        if not request.user.is_authenticated or request.user != post.author:
            raise Http404

    comment_form = CommentForm()
    comments = post.comments.order_by('created_at')
    context = {'post': post, 'comment_form': comment_form, 'comments': comments}
    return render(request, template, context=context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    posts_qs = Post.objects.select_related('location', 'category', 'author').filter(
        Q(pub_date__lte=timezone.now())
        & Q(is_published__exact=True)
        & Q(category__is_published__exact=True)
        & Q(category__slug__exact=category_slug)
    ).order_by('-pub_date')
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'post_list': page_obj.object_list, 'category': category, 'page_obj': page_obj}
    return render(request, template, context=context)


def profile(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    if request.user.is_authenticated and request.user == user:
        posts_qs = Post.objects.filter(author=user).select_related('location', 'category', 'author').order_by('-pub_date')
    else:
        posts_qs = Post.objects.filter(author=user).select_related('location', 'category', 'author').filter(
            Q(pub_date__lte=timezone.now()) & Q(is_published__exact=True) & Q(category__is_published__exact=True)
        ).order_by('-pub_date')
    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'profile_user': user, 'post_list': page_obj.object_list, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context=context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.author != request.user:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required
@require_http_methods(["GET", "POST"])
def delete_post(request, id):
    post = get_object_or_404(Post, pk=id)
    if post.author != request.user and not request.user.is_staff:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    # render confirmation using detail template
    return render(request, 'blog/detail.html', {'post': post, 'confirm_delete': True})


@login_required
def add_comment(request, id):
    post = get_object_or_404(Post, pk=id)
    if request.method != 'POST':
        return redirect('blog:post_detail', id=post.id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    from .models import Comment
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    if comment.author != request.user:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', id=post.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/comment_edit.html', {'form': form, 'post': post, 'comment': comment})


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    from .models import Comment
    comment = get_object_or_404(Comment, pk=comment_id, post=post)
    if comment.author != request.user and not request.user.is_staff:
        return redirect('blog:post_detail', id=post.id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', id=post.id)
    return render(request, 'blog/comment_edit.html', {'comment': comment, 'post': post, 'confirm_delete': True})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/registration_form.html', {'form': form})


@login_required
def edit_profile(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect('blog:profile', username=username)
    from django import forms
    class _Form(forms.ModelForm):
        class Meta:
            model = User
            fields = ('first_name', 'last_name', 'username', 'email')

    if request.method == 'POST':
        form = _Form(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = _Form(instance=user)
    return render(request, 'registration/registration_form.html', {'form': form})
