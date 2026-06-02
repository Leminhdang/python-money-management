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
        description=(
            "**Hệ thống Backend RESTful API quản lý thu chi cá nhân**\n\n"
            "Đồ án kết thúc môn Kĩ thuật lập trình Python — UIT.\n\n"
            "### Tính năng chính:\n"
            "- Xác thực JWT (đăng ký, đăng nhập, profile)\n"
            "- CRUD Ví, Danh mục, Giao dịch, Ngân sách, Thông báo\n"
            "- Giao dịch nguyên tử (auto trừ ví + trừ ngân sách + sinh cảnh báo)\n"
            "- Chuyển khoản nội bộ giữa 2 ví\n"
            "- Thống kê dòng tiền, tỷ lệ chi tiêu, biến động theo ngày\n\n"
            "### Module OOP tự xây dựng:\n"
            "- **phan_tich_chi_tieu.py**: Phân tích đa hình (theo ngày / danh mục / ví)\n"
            "- **xuat_bao_cao.py**: Xuất báo cáo đa định dạng (JSON / CSV / Text)\n\n"
            "### Xác thực:\n"
            "1. Gọi `POST /api/v1/users/login/` để lấy token\n"
            "2. Click nút **Authorize** → nhập `Bearer <access_token>`\n"
        ),
        contact=openapi.Contact(email="leminhdang@gmail.com"),
        license=openapi.License(name="MIT License"),
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
