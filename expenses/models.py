import uuid
from django.db import models
from django.conf import settings


# Enum loại giao dịch: Thu nhập hoặc Chi tiêu
class TransactionType(models.TextChoices):
    INCOME = 'income', 'Thu nhập'
    EXPENSE = 'expense', 'Chi tiêu'


class Category(models.Model):
    """Danh mục thu/chi, hỗ trợ phân cấp cha-con (đệ quy)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")

    # Liên kết user sở hữu danh mục này
    userId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Người dùng"
    )

    # Liên kết đệ quy – danh mục cha (có thể null nếu là gốc)
    parentId = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Danh mục cha"
    )

    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name="Loại danh mục"
    )

    class Meta:
        verbose_name = "Danh mục"
        verbose_name_plural = "Danh sách danh mục"

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Wallet(models.Model):
    """Ví tiền (tài khoản thanh toán) của người dùng."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    userId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
        verbose_name="Người dùng"
    )

    name = models.CharField(max_length=100, verbose_name="Tên ví")
    type = models.CharField(max_length=50, verbose_name="Loại ví")  # VD: Tiền mặt, ATM, Momo...
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, verbose_name="Số dư")

    class Meta:
        verbose_name = "Ví"
        verbose_name_plural = "Danh sách ví"

    def __str__(self):
        return f"{self.name} ({self.amount} đ)"


class Transaction(models.Model):
    """Giao dịch thu/chi, gắn với 1 ví và 1 danh mục."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    walletId = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Ví giao dịch"
    )

    # Danh mục có thể null nếu bị xóa sau này
    categoryId = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Danh mục"
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền")
    type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
        verbose_name="Loại giao dịch"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Thời gian tạo")

    class Meta:
        verbose_name = "Giao dịch"
        verbose_name_plural = "Danh sách giao dịch"

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} đ ({self.walletId.name})"



class Budget(models.Model):
    """Hạn mức ngân sách cho 1 danh mục, áp dụng cho nhiều ví."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Tên ngân sách")

    categoryId = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name="Danh mục áp dụng"
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền ngân sách")
    remain = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền còn lại")
    loop = models.BooleanField(default=False, verbose_name="Tự động lặp lại")
    fromDate = models.DateField(verbose_name="Ngày bắt đầu")
    toDate = models.DateField(verbose_name="Ngày kết thúc")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")

    # Quan hệ N-N với Wallet qua bảng trung gian
    wallets = models.ManyToManyField(
        Wallet,
        through='Budget_Wallets',
        related_name='budgets',
        verbose_name="Các ví áp dụng"
    )

    class Meta:
        verbose_name = "Ngân sách"
        verbose_name_plural = "Danh sách ngân sách"

    def __str__(self):
        return f"{self.name} ({self.amount} đ)"


class Budget_Wallets(models.Model):
    """Bảng trung gian N-N giữa Budget và Wallet.
    Dùng ID tự tăng mặc định của Django, ko dùng UUID.
    """

    budgetId = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        verbose_name="Ngân sách"
    )
    walletId = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        verbose_name="Ví"
    )

    class Meta:
        verbose_name = "Liên kết Ngân sách - Ví"
        verbose_name_plural = "Liên kết Ngân sách - Ví"
        unique_together = ('budgetId', 'walletId')  # tránh trùng cặp

    def __str__(self):
        return f"Budget: {self.budgetId.name} - Wallet: {self.walletId.name}"


class Notification(models.Model):
    """Thông báo cảnh báo gửi cho user (vd: ngân sách sắp hết)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    userId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Người dùng"
    )

    content = models.TextField(verbose_name="Nội dung thông báo")
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name="Liên kết (Deeplink)")
    time = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    isRead = models.BooleanField(default=False, verbose_name="Đã đọc")

    class Meta:
        verbose_name = "Thông báo"
        verbose_name_plural = "Danh sách thông báo"

    def __str__(self):
        trang_thai = "Đã đọc" if self.isRead else "Chưa đọc"
        return f"Thông báo cho {self.userId.username} ({trang_thai}): {self.content[:30]}..."
