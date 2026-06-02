from rest_framework import serializers
from .models import Category, Wallet, Transaction, Budget, Notification


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho Category – hỗ trợ hiển thị danh mục con lồng nhau (đệ quy).
    Khi GET danh mục cha sẽ tự kéo theo mảng subcategories bên trong.
    """
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'userId', 'parentId', 'type', 'subcategories')
        read_only_fields = ('id', 'userId')

    def get_subcategories(self, obj):
        # Lấy danh mục con rồi đệ quy gọi lại chính serializer này
        sub_categories = obj.subcategories.all()
        return CategorySerializer(sub_categories, many=True).data


class WalletSerializer(serializers.ModelSerializer):
    """Serializer cho Ví tài chính."""

    class Meta:
        model = Wallet
        fields = ('id', 'userId', 'name', 'type', 'amount')
        read_only_fields = ('id', 'userId')

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("Số dư ví ko được nhỏ hơn 0.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer cho Giao dịch Thu/Chi."""

    class Meta:
        model = Transaction
        fields = ('id', 'walletId', 'categoryId', 'amount', 'type', 'note')
        read_only_fields = ('id',)

    def validate_amount(self, value):
        # Số tiền giao dịch phải > 0
        if value <= 0:
            raise serializers.ValidationError("Số tiền giao dịch bắt buộc phải lớn hơn 0.")
        return value

    def validate(self, data):
        # Check xem loại giao dịch có khớp với loại danh mục ko
        category = data.get('categoryId')
        transaction_type = data.get('type')
        if category and category.type != transaction_type:
            raise serializers.ValidationError(
                {"type": f"Loại giao dịch ({transaction_type}) không khớp với loại danh mục ({category.type})."}
            )
        return data


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer cho Ngân sách.
    Tự xử lý quan hệ N-N với Wallet qua bảng trung gian Budget_Wallets.
    """
    # wallets nhận list UUID ví khi POST/PUT
    wallets = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Wallet.objects.all(),
        required=False
    )

    class Meta:
        model = Budget
        fields = ('id', 'name', 'categoryId', 'amount', 'remain', 'loop', 'fromDate', 'toDate', 'note', 'wallets')
        read_only_fields = ('id', 'remain')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Hạn mức ngân sách phải lớn hơn 0.")
        return value

    def validate_remain(self, value):
        if value < 0:
            raise serializers.ValidationError("Số tiền còn lại ko được âm.")
        return value

    def validate(self, data):
        # Ngày kết thúc ko được trước ngày bắt đầu
        from_date = data.get('fromDate')
        to_date = data.get('toDate')
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError(
                {"toDate": "Ngày kết thúc ko thể nhỏ hơn ngày bắt đầu."}
            )
        return data


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer cho Thông báo hệ thống."""

    class Meta:
        model = Notification
        fields = ('id', 'userId', 'content', 'link', 'time', 'isRead')
        read_only_fields = ('id', 'userId', 'time')
