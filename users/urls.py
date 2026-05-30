from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterAPIView, LoginAPIView, UserProfileAPIView, UserAdminViewSet

# Sử dụng DefaultRouter để tự động tạo các RESTful endpoints cho Admin quản lý User
router = DefaultRouter()
router.register('users/admin', UserAdminViewSet, basename='user-admin')

urlpatterns = [
    # Các API xác thực và tài khoản cá nhân
    path('users/register/', RegisterAPIView.as_view(), name='user-register'),
    path('users/login/', LoginAPIView.as_view(), name='user-login'),
    path('users/profile/', UserProfileAPIView.as_view(), name='user-profile'),
    
    # Định tuyến cho Admin ViewSet
    path('', include(router.urls)),
]
