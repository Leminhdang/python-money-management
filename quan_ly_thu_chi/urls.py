"""
Cấu hình URL chính cho project Quản Lý Thu Chi.
Gom toàn bộ API dưới prefix api/v1/.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Cấu hình Swagger schema
schema_view = get_schema_view(
    openapi.Info(
        title="API Quản Lý Thu Chi",
        default_version='v1',
        description="Tài liệu API cho hệ thống quản lý thu chi cá nhân",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Gom toàn bộ API dưới tiền tố api/v1/
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('expenses.urls')),

    # Swagger UI va ReDoc
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
