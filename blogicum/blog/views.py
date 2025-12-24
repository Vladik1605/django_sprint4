from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from .forms import CommentForm, PostForm, RegistrationForm
from .models import Category, Comment, Post

User = get_user_model()


class PostListView(ListView):
    """Display list of published posts with pagination."""

    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        return (
            Post.objects
            .select_related('location', 'category', 'author')
            .prefetch_related('comments')
            .filter(
                Q(pub_date__lte=timezone.now())
                & Q(is_published__exact=True)
                & Q(category__is_published__exact=True)
            )
            .order_by('-pub_date')
        )


index = PostListView.as_view()


class PostDetailView(DetailView):
    """Display detailed post view with comments."""

    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return (
            Post.objects
            .select_related('location', 'category', 'author')
            .prefetch_related('comments__author')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()

        # Check visibility
        is_published = (
            post.pub_date <= timezone.now()
            and post.is_published
            and post.category
            and post.category.is_published
        )
        if not is_published:
            # Allow author to see own unpublished/scheduled posts
            if (
                not self.request.user.is_authenticated
                or self.request.user != post.author
            ):
                raise Http404

        comment_form = CommentForm()
        comments = post.comments.order_by('created_at')
        context['comment_form'] = comment_form
        context['comments'] = comments
        return context


post_detail = PostDetailView.as_view()


class CategoryPostListView(ListView):
    """Display published posts in specific category."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return (
            Post.objects
            .select_related('location', 'category', 'author')
            .prefetch_related('comments')
            .filter(
                Q(pub_date__lte=timezone.now())
                & Q(is_published__exact=True)
                & Q(category__is_published__exact=True)
                & Q(category__slug__exact=self.kwargs['category_slug'])
            )
            .order_by('-pub_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


category_posts = CategoryPostListView.as_view()


class ProfileView(ListView):
    """Display user profile with their posts."""

    model = Post
    template_name = 'blog/profile.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.profile_user = get_object_or_404(
            User, username=self.kwargs['username']
        )

        posts_qs = Post.objects.filter(author=self.profile_user).select_related(
            'location', 'category', 'author'
        ).prefetch_related('comments')

        # Show all posts if viewing own profile, else only published
        if (
            self.request.user.is_authenticated
            and self.request.user == self.profile_user
        ):
            return posts_qs.order_by('-pub_date')
        else:
            return (
                posts_qs
                .filter(
                    Q(pub_date__lte=timezone.now())
                    & Q(is_published__exact=True)
                    & Q(category__is_published__exact=True)
                )
                .order_by('-pub_date')
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_user'] = self.profile_user
        return context


profile = ProfileView.as_view()


class CreatePostView(CreateView):
    """Create new post."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        if not form.instance.pub_date:
            form.instance.pub_date = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


create_post = login_required(CreatePostView.as_view())


class EditPostView(UpdateView):
    """Edit existing post."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def form_valid(self, form):
        if not form.instance.pub_date:
            form.instance.pub_date = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'id': self.object.pk}
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user:
            raise Http404('You are not the author of this post.')
        return obj


edit_post = login_required(EditPostView.as_view())


class DeletePostView(DeleteView):
    """Delete post with confirmation."""

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('blog:index')

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user and not self.request.user.is_staff:
            raise Http404('You are not the author of this post.')
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['confirm_delete'] = True
        return context


delete_post = login_required(DeletePostView.as_view())


class AddCommentView(SingleObjectMixin, FormView):
    """Add comment to post."""

    model = Post
    form_class = CommentForm
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = self.object
        comment.author = self.request.user
        comment.save()
        return redirect('blog:post_detail', id=self.object.pk)


add_comment = login_required(AddCommentView.as_view())


class EditCommentView(UpdateView):
    """Edit existing comment."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment_edit.html'
    pk_url_kwarg = 'comment_id'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(
            Post, pk=self.kwargs['post_id']
        )
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'id': self.object.post.pk}
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user:
            raise Http404('You are not the author of this comment.')
        return obj


edit_comment = login_required(EditCommentView.as_view())


class DeleteCommentView(DeleteView):
    """Delete comment with confirmation."""

    model = Comment
    template_name = 'blog/comment_edit.html'
    pk_url_kwarg = 'comment_id'

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'id': self.object.post.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = get_object_or_404(
            Post, pk=self.kwargs['post_id']
        )
        context['confirm_delete'] = True
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author != self.request.user and not self.request.user.is_staff:
            raise Http404('You are not the author of this comment.')
        return obj


delete_comment = login_required(DeleteCommentView.as_view())


class RegistrationView(CreateView):
    """User registration."""

    form_class = RegistrationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


register = RegistrationView.as_view()


class EditProfileView(UpdateView):
    """Edit user profile."""

    model = User
    fields = ('first_name', 'last_name', 'username', 'email')
    template_name = 'registration/registration_form.html'

    def get_object(self, queryset=None):
        user = get_object_or_404(User, username=self.kwargs['username'])
        if user != self.request.user:
            raise Http404('You can only edit your own profile.')
        return user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.object.username}
        )


edit_profile = login_required(EditProfileView.as_view())
