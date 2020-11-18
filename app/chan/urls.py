from django.urls import path, include

from rest_framework.routers import DefaultRouter

from chan.views import (
    BoardViewSet, ManageThreadViewSet
)


router = DefaultRouter()
router.register('boards', BoardViewSet)
router.register('thread', ManageThreadViewSet)


app_name = '6chan'
urlpatterns = [
    path('', include(router.urls)),
]
