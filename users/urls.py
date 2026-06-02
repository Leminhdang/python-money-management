from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAPIView, LoginAPIView, UserProfileAPIView, UserAdminViewSet

# Router cho Admin quản lý user
router = DefaultRouter()
router.register('users/admin', UserAdminViewSet, basename='user-admin')

urlpatterns = [
    # API xác thực và tài khoản
    path('users/register/', RegisterAPIView.as_view(), name='user-register'),
    path('users/login/', LoginAPIView.as_view(), name='user-login'),
    path('users/profile/', UserProfileAPIView.as_view(), name='user-profile'),

    path('', include(router.urls)),
]
