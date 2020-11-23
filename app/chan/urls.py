from django.urls import path, include

from rest_framework.routers import DefaultRouter

from chan.views import (
    BoardViewSet, ManageThreadViewSet, ManageReplyViewSet
)


router = DefaultRouter()
router.register('boards', BoardViewSet)
router.register('thread', ManageThreadViewSet)
router.register('reply', ManageReplyViewSet)


app_name = '6chan'
urlpatterns = [
    path('', include(router.urls)),
]
