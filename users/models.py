import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Model User tùy chỉnh, kế thừa AbstractUser của Django."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255, verbose_name="Họ và tên")
    birthday = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    phoneNumber = models.CharField(max_length=20, null=True, blank=True, verbose_name="Số điện thoại")
    address = models.TextField(null=True, blank=True, verbose_name="Địa chỉ")

    # Email bắt buộc unique để dùng cho đăng nhập
    email = models.EmailField(unique=True, verbose_name="Email")

    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    # Giữ username làm trường đăng nhập mặc định của AbstractUser
    # Nếu sau này muốn login bằng email thì đổi USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Danh sách người dùng"

    def __str__(self):
        return self.email or self.username
