import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Sử dụng UUID làm Khóa chính
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Bổ sung các thuộc tính theo yêu cầu
    name = models.CharField(max_length=255, verbose_name="Họ và tên")
    birthday = models.DateField(null=True, blank=True, verbose_name="Ngày sinh")
    phoneNumber = models.CharField(max_length=20, null=True, blank=True, verbose_name="Số điện thoại")
    address = models.TextField(null=True, blank=True, verbose_name="Địa chỉ")
    
    # Email phải là duy nhất
    email = models.EmailField(unique=True, verbose_name="Email")
    
    # Thời điểm tạo tài khoản
    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")

    # Sử dụng email làm trường thông tin đăng nhập chính (tùy chọn nhưng khuyến nghị cho Web API hiện đại)
    # Ở đây chúng ta kế thừa mặc định của AbstractUser vẫn giữ username, nhưng yêu cầu email unique.
    # Ta có thể thiết lập:
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username', 'name']
    
    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Danh sách người dùng"

    def __str__(self):
        return self.email or self.username
