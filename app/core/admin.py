from django.contrib import admin

from core.models import User, Board, Thread, Reply


admin.site.register(User)
admin.site.register(Board)
admin.site.register(Thread)
admin.site.register(Reply)
