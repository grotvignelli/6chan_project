from django.contrib import admin

from core.models import User, Board, Thread


admin.site.register(User)
admin.site.register(Board)
admin.site.register(Thread)
