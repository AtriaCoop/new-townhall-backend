from django.contrib import admin

from .models import User, Tag

admin.site.register(User)
admin.site.register(Tag)
