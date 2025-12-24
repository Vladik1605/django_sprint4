# Register your models here.
from django.contrib import admin
from blog.models import Category, Location, Post


admin.site.register(Location)
admin.site.register(Category)
admin.site.register(Post)
