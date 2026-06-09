"""
Cấu hình URL chính cho project Quản Lý Thu Chi.
Gom toàn bộ API dưới prefix api/v1/.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Gom toàn bộ API dưới tiền tố api/v1/
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('expenses.urls')),
]
