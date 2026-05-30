from rest_framework import serializers
from .models import Category, Wallet, Transaction, Budget, Notification

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer cho Category hỗ trợ quan hệ đệ quy lồng nhau (Nested Serializer).
    Khi GET một danh mục cha, nó sẽ tự động lồng mảng các danh mục con tương ứng.
    """
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'userId', 'parentId', 'type', 'subcategories')
        read_only_fields = ('id',)

    def get_subcategories(self, obj):
        # Lấy tất cả các danh mục con của danh mục hiện tại
        sub_categories = obj.subcategories.all()
        # Đệ quy tự gọi lại chính CategorySerializer để hiển thị đa cấp
        return CategorySerializer(sub_categories, many=True).data


class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer quản lý Ví tài chính cá nhân.
    """
    class Meta:
        model = Wallet
        fields = ('id', 'userId', 'name', 'type', 'amount')
        read_only_fields = ('id',)

    def validate_amount(self, value):
        # Đảm bảo số tiền khởi tạo không âm
        if value < 0:
            raise serializers.ValidationError("Số dư tài khoản ví không được nhỏ hơn 0.")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer quản lý các Giao dịch Thu/Chi.
    """
    class Meta:
        model = Transaction
        fields = ('id', 'walletId', 'categoryId', 'amount', 'type', 'note')
        read_only_fields = ('id',)

    def validate_amount(self, value):
        # 5. Hàm validate số tiền giao dịch phải lớn hơn 0
        if value <= 0:
            raise serializers.ValidationError("Số tiền giao dịch bắt buộc phải lớn hơn 0.")
        return value

    def validate(self, data):
        # Kiểm tra logic nghiệp vụ: loại giao dịch trong transaction có trùng khớp với loại danh mục không
        category = data.get('categoryId')
        transaction_type = data.get('type')
        if category and category.type != transaction_type:
            raise serializers.ValidationError(
                {"type": f"Loại giao dịch ({transaction_type}) không trùng khớp với loại danh mục ({category.type})."}
            )
        return data


class BudgetSerializer(serializers.ModelSerializer):
    """
    Serializer quản lý Ngân sách chi tiêu/thu nhập.
    Tự động xử lý quan hệ Many-to-Many với Wallet thông qua bảng trung gian Budget_Wallets.
    """
    # wallets nhận danh sách UUID ví khi gửi request POST/PUT
    wallets = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Wallet.objects.all(),
        required=False
    )

    class Meta:
        model = Budget
        fields = ('id', 'name', 'categoryId', 'amount', 'remain', 'loop', 'fromDate', 'toDate', 'note', 'wallets')
        read_only_fields = ('id',)

    def validate_amount(self, value):
        # 5. Hàm validate hạn mức ngân sách phải lớn hơn 0
        if value <= 0:
            raise serializers.ValidationError("Số tiền hạn mức ngân sách bắt buộc phải lớn hơn 0.")
        return value

    def validate_remain(self, value):
        # Đảm bảo số dư ngân sách còn lại lớn hơn hoặc bằng 0
        if value < 0:
            raise serializers.ValidationError("Số tiền còn lại của ngân sách không được nhỏ hơn 0.")
        return value

    def validate(self, data):
        # Kiểm tra logic nghiệp vụ: thời gian bắt đầu và kết thúc
        from_date = data.get('fromDate')
        to_date = data.get('toDate')
        if from_date and to_date and to_date < from_date:
            raise serializers.ValidationError(
                {"toDate": "Ngày kết thúc ngân sách không thể nhỏ hơn ngày bắt đầu."}
            )
        return data


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer quản lý các Thông báo hệ thống.
    """
    class Meta:
        model = Notification
        fields = ('id', 'userId', 'content', 'link', 'time', 'isRead')
        read_only_fields = ('id', 'time')
