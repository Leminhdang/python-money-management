import uuid
from django.db import models
from django.conf import settings

class TransactionType(models.TextChoices):
    INCOME = 'income', 'Thu nhập'
    EXPENSE = 'expense', 'Chi tiêu'

class Category(models.Model):
    # Khóa chính UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Tên danh mục")
    
    # userId liên kết với bảng User, xóa cascade
    userId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Người dùng"
    )
    
    # parentId liên kết đệ quy chính nó, xóa set null
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
    # Khóa chính UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # userId liên kết với bảng User, xóa cascade
    userId = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
        verbose_name="Người dùng"
    )
    
    name = models.CharField(max_length=100, verbose_name="Tên ví")
    type = models.CharField(max_length=50, verbose_name="Loại ví")  # Ví điện tử, Tiền mặt, ATM...
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, verbose_name="Số dư")

    class Meta:
        verbose_name = "Ví"
        verbose_name_plural = "Danh sách ví"

    def __str__(self):
        return f"{self.name} ({self.amount} đ)"


class Transaction(models.Model):
    # Khóa chính UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # walletId liên kết với ví, xóa cascade
    walletId = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Ví giao dịch"
    )
    
    # categoryId liên kết với danh mục, xóa set null
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
    
    # Thời gian tạo giao dịch phục vụ thống kê dòng tiền
    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Thời gian tạo")

    class Meta:
        verbose_name = "Giao dịch"
        verbose_name_plural = "Danh sách giao dịch"

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} đ ({self.walletId.name})"



class Budget(models.Model):
    # Khóa chính UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Tên ngân sách")
    
    # categoryId liên kết với danh mục, xóa cascade
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
    
    # Mối quan hệ Many-to-Many với Wallet thông qua bảng trung gian Budget_Wallets
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
    # Bảng trung gian Many-to-Many giữa Budget và Wallet
    # Không dùng UUID làm khóa chính theo yêu cầu (sử dụng ID tự tăng mặc định của Django)
    
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
        unique_together = ('budgetId', 'walletId')  # Tránh tạo trùng cặp liên kết

    def __str__(self):
        return f"Budget: {self.budgetId.name} - Wallet: {self.walletId.name}"


class Notification(models.Model):
    # Khóa chính UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # userId liên kết User, xóa cascade
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
        status = "Đã đọc" if self.isRead else "Chưa đọc"
        return f"Thông báo cho {self.userId.username} ({status}): {self.content[:30]}..."
