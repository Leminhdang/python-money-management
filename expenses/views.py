from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.db.models.functions import TruncDate
from decimal import Decimal

from .models import Category, Wallet, Transaction, Budget, Notification
from .serializers import (
    CategorySerializer,
    WalletSerializer,
    TransactionSerializer,
    BudgetSerializer,
    NotificationSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý Danh mục thu/chi.
    - Người dùng thông thường chỉ thao tác trên danh mục của riêng họ.
    - Admin (IsAdminUser) có thể quản lý tất cả các danh mục trên hệ thống.
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer

    def get_permissions(self):
        # Thiết lập quyền: Chỉ Admin mới có thể xóa hoặc sửa đổi danh mục hệ thống
        if self.action in ['destroy', 'update', 'partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Trả về danh mục thuộc về người dùng hiện tại
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Category.objects.all()
        return Category.objects.filter(userId=self.request.user)

    def perform_create(self, serializer):
        # Tự động gán người dùng hiện tại làm chủ sở hữu danh mục
        serializer.save(userId=self.request.user)


class WalletViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý các Ví tiền (tài khoản thanh toán).
    Tất cả các API yêu cầu xác thực người dùng và chỉ trả về ví của chính họ.
    """
    queryset = Wallet.objects.all().order_by('name')
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(userId=self.request.user)

    def perform_create(self, serializer):
        serializer.save(userId=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý Giao dịch Thu/Chi.
    Chứa toàn bộ logic nghiệp vụ tự động hóa số dư Ví, Hạn mức Ngân sách và Thông báo.
    """
    queryset = Transaction.objects.all().order_by('-createdAt')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Chỉ lấy các giao dịch thuộc các ví của người dùng hiện tại
        return Transaction.objects.filter(walletId__userId=self.request.user)

    @db_transaction.atomic
    def perform_create(self, serializer):
        wallet = serializer.validated_data['walletId']
        
        # Kiểm tra tính chính chủ của ví
        if wallet.userId != self.request.user:
            raise serializers.ValidationError({"walletId": "Ví giao dịch không thuộc quyền sở hữu của bạn."})
        
        # Lưu giao dịch mới
        transaction = serializer.save()
        
        # TỰ ĐỘNG HÓA LOGIC 1: Cập nhật số dư Ví (Cộng tiền nếu là Thu, Trừ tiền nếu là Chi)
        amount = transaction.amount
        if transaction.type == 'expense':
            wallet.amount -= amount
        else:
            wallet.amount += amount
        wallet.save()

        # TỰ ĐỘNG HÓA LOGIC 2: Trừ hạn mức ngân sách và bắn cảnh báo khi có chi tiêu (expense)
        if transaction.type == 'expense':
            today = timezone.localdate()
            # Tìm kiếm các ngân sách đang chạy thuộc danh mục chi tiêu này và áp dụng cho ví này
            active_budgets = Budget.objects.filter(
                categoryId=transaction.categoryId,
                wallets=wallet,
                fromDate__lte=today,
                toDate__gte=today
            )
            for budget in active_budgets:
                budget.remain -= amount
                budget.save()
                
                # Tự động sinh thông báo cảnh báo nếu ngân sách cạn kiệt hoặc âm
                if budget.remain <= 0:
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' dành cho ví '{wallet.name}' đã cạn kiệt hoặc bị âm! Số tiền còn lại: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )
                # Cảnh báo nếu ngân sách còn lại dưới 10%
                elif budget.remain < (budget.amount * Decimal('0.10')):
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' dành cho ví '{wallet.name}' sắp hết! Số tiền còn lại dưới 10%: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )

    @db_transaction.atomic
    def perform_update(self, serializer):
        old_instance = self.get_object()
        
        # Hoàn trả lại số dư cũ cho ví cũ trước khi cập nhật
        old_wallet = old_instance.walletId
        if old_instance.type == 'expense':
            old_wallet.amount += old_instance.amount
        else:
            old_wallet.amount -= old_instance.amount
        old_wallet.save()
        
        # Hoàn trả lại hạn mức ngân sách cũ (nếu có)
        if old_instance.type == 'expense':
            today = timezone.localdate()
            old_budgets = Budget.objects.filter(
                categoryId=old_instance.categoryId,
                wallets=old_wallet,
                fromDate__lte=today,
                toDate__gte=today
            )
            for budget in old_budgets:
                budget.remain += old_instance.amount
                budget.save()

        # Lưu thông tin giao dịch mới cập nhật
        new_transaction = serializer.save()
        new_wallet = new_transaction.walletId
        
        # Kiểm tra tính hợp lệ của ví mới
        if new_wallet.userId != self.request.user:
            raise serializers.ValidationError({"walletId": "Ví giao dịch mới không thuộc sở hữu của bạn."})

        # Áp dụng số dư mới cho ví mới
        new_amount = new_transaction.amount
        if new_transaction.type == 'expense':
            new_wallet.amount -= new_amount
        else:
            new_wallet.amount += new_amount
        new_wallet.save()

        # Áp dụng thay đổi vào ngân sách mới (nếu có)
        if new_transaction.type == 'expense':
            today = timezone.localdate()
            new_budgets = Budget.objects.filter(
                categoryId=new_transaction.categoryId,
                wallets=new_wallet,
                fromDate__lte=today,
                toDate__gte=today
            )
            for budget in new_budgets:
                budget.remain -= new_amount
                budget.save()
                
                # Bắn cảnh báo nếu ngân sách cạn kiệt
                if budget.remain <= 0:
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' đã cạn kiệt hoặc bị âm sau khi cập nhật giao dịch! Số tiền còn lại: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )
                elif budget.remain < (budget.amount * Decimal('0.10')):
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' sắp hết sau khi cập nhật giao dịch! Số tiền còn lại dưới 10%: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )

    @db_transaction.atomic
    def perform_destroy(self, instance):
        wallet = instance.walletId
        
        # Hoàn trả lại tiền vào ví khi xóa giao dịch
        if instance.type == 'expense':
            wallet.amount += instance.amount
        else:
            wallet.amount -= instance.amount
        wallet.save()

        # Hoàn trả lại hạn mức cho ngân sách liên quan
        if instance.type == 'expense':
            today = timezone.localdate()
            budgets = Budget.objects.filter(
                categoryId=instance.categoryId,
                wallets=wallet,
                fromDate__lte=today,
                toDate__gte=today
            )
            for budget in budgets:
                budget.remain += instance.amount
                budget.save()
                
        instance.delete()

    # --- 3. CÁC API THỐNG KÊ VÀ BÁO CÁO ---

    @action(detail=False, methods=['get'], url_path='reports/summary')
    def reports_summary(self, request):
        """
        API tổng hợp: Tổng thu, tổng chi, số dư ròng trong tháng hiện tại.
        GET /api/v1/expenses/transactions/reports/summary/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)
        
        # Lọc giao dịch của user trong tháng hiện tại
        txs = self.get_queryset().filter(createdAt__date__gte=start_of_month, createdAt__date__lte=today)
        
        total_income = txs.filter(type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        total_expense = txs.filter(type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        net_balance = total_income - total_expense
        
        return Response({
            "month": today.strftime('%m/%Y'),
            "totalIncome": total_income,
            "totalExpense": total_expense,
            "netBalance": net_balance
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='reports/categories')
    def reports_categories(self, request):
        """
        API tỷ lệ % chi tiêu theo từng danh mục trong tháng hiện tại.
        GET /api/v1/expenses/transactions/reports/categories/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)
        
        # Lọc các giao dịch CHI TIÊU của user trong tháng hiện tại
        expenses = self.get_queryset().filter(
            type='expense',
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        )
        
        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.0')
        
        if total_expense == 0:
            return Response({"message": "Không có giao dịch chi tiêu nào trong tháng.", "data": []}, status=status.HTTP_200_OK)
            
        # Gom nhóm theo danh mục và tính tổng số tiền
        category_stats = expenses.values('categoryId__name').annotate(total_amount=Sum('amount')).order_by('-total_amount')
        
        report_data = []
        for stat in category_stats:
            cat_name = stat['categoryId__name'] or "Không xác định"
            amount = stat['total_amount'] or Decimal('0.0')
            percentage = round((amount / total_expense) * 100, 2)
            report_data.append({
                "categoryName": cat_name,
                "amount": amount,
                "percentage": percentage
            })
            
        return Response({
            "month": today.strftime('%m/%Y'),
            "totalExpense": total_expense,
            "data": report_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='reports/daily')
    def reports_daily(self, request):
        """
        API dòng tiền biến động Thu vs Chi theo từng ngày trong tháng hiện tại.
        GET /api/v1/expenses/transactions/reports/daily/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)
        
        txs = self.get_queryset().filter(createdAt__date__gte=start_of_month, createdAt__date__lte=today)
        
        # Gom nhóm theo ngày và tính tổng thu/chi
        daily_stats = txs.annotate(date=TruncDate('createdAt')).values('date', 'type').annotate(total_amount=Sum('amount')).order_by('date')
        
        # Tổ chức lại cấu trúc dữ liệu theo ngày
        data_by_date = {}
        for stat in daily_stats:
            date_str = stat['date'].strftime('%Y-%m-%d')
            if date_str not in data_by_date:
                data_by_date[date_str] = {"date": date_str, "income": Decimal('0.0'), "expense": Decimal('0.0')}
            
            if stat['type'] == 'income':
                data_by_date[date_str]['income'] = stat['total_amount']
            else:
                data_by_date[date_str]['expense'] = stat['total_amount']
                
        return Response(list(data_by_date.values()), status=status.HTTP_200_OK)

    # --- 4. API CHUYỂN KHOẢN (TRANSFER) ---

    @action(detail=False, methods=['post'], url_path='transfer')
    @db_transaction.atomic
    def transfer(self, request):
        """
        API Chuyển khoản nội bộ giữa các Ví tài chính của người dùng.
        POST /api/v1/expenses/transactions/transfer/
        Payload: {"fromWalletId": "UUID", "toWalletId": "UUID", "amount": 50000.0, "note": "Chuyển tiền tiết kiệm"}
        """
        from_wallet_id = request.data.get('fromWalletId')
        to_wallet_id = request.data.get('toWalletId')
        amount_raw = request.data.get('amount')
        note = request.data.get('note', '')

        # Kiểm tra tham số đầu vào
        if not from_wallet_id or not to_wallet_id or not amount_raw:
            return Response({"error": "Vui lòng cung cấp đầy đủ thông tin: fromWalletId, toWalletId, amount"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(amount_raw))
        except ValueError:
            return Response({"error": "Số tiền chuyển khoản không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Số tiền chuyển khoản phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy thông tin Ví từ cơ sở dữ liệu
        try:
            from_wallet = Wallet.objects.get(id=from_wallet_id, userId=request.user)
            to_wallet = Wallet.objects.get(id=to_wallet_id, userId=request.user)
        except Wallet.DoesNotExist:
            return Response({"error": "Một hoặc cả hai Ví không tồn tại hoặc không thuộc quyền sở hữu của bạn."}, status=status.HTTP_404_NOT_FOUND)

        if from_wallet.id == to_wallet.id:
            return Response({"error": "Không thể chuyển khoản đến chính ví hiện tại."}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra số dư tài khoản ví nguồn
        if from_wallet.amount < amount:
            return Response({"error": f"Số dư ví nguồn không đủ để thực hiện giao dịch này. Số dư hiện tại: {from_wallet.amount} đ."}, status=status.HTTP_400_BAD_REQUEST)

        # Thực hiện trừ tiền ở ví gửi và cộng tiền ở ví nhận
        from_wallet.amount -= amount
        from_wallet.save()
        
        to_wallet.amount += amount
        to_wallet.save()

        # Tạo danh mục mặc định dành cho chuyển khoản nếu chưa có
        category_transfer, _ = Category.objects.get_or_create(
            name="Chuyển khoản nội bộ",
            userId=request.user,
            type=TransactionType.EXPENSE,
            defaults={"parentId": None}
        )

        # Tạo lịch sử giao dịch chi tiêu (Ghi nhận ở ví gửi)
        tx_from = Transaction.objects.create(
            walletId=from_wallet,
            categoryId=category_transfer,
            amount=amount,
            type='expense',
            note=f"Chuyển khoản đến Ví '{to_wallet.name}'. Ghi chú: {note}"
        )

        # Tạo lịch sử giao dịch thu nhập (Ghi nhận ở ví nhận)
        tx_to = Transaction.objects.create(
            walletId=to_wallet,
            categoryId=category_transfer,
            amount=amount,
            type='income',
            note=f"Nhận chuyển khoản từ Ví '{from_wallet.name}'. Ghi chú: {note}"
        )

        return Response({
            "message": "Chuyển khoản nội bộ thành công!",
            "fromWallet": WalletSerializer(from_wallet).data,
            "toWallet": WalletSerializer(to_wallet).data,
            "transactions": [
                TransactionSerializer(tx_from).data,
                TransactionSerializer(tx_to).data
            ]
        }, status=status.HTTP_200_OK)


class BudgetViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý Hạn mức Ngân sách.
    """
    queryset = Budget.objects.all().order_by('-fromDate')
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Trả về ngân sách có danh mục thuộc sở hữu của người dùng hiện tại
        return Budget.objects.filter(categoryId__userId=self.request.user)

    def perform_create(self, serializer):
        # Tự động khởi tạo số dư còn lại (remain) bằng đúng số tiền thiết lập ban đầu (amount)
        amount = serializer.validated_data.get('amount', Decimal('0.0'))
        serializer.save(remain=amount)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý Thông báo cảnh báo của hệ thống.
    """
    queryset = Notification.objects.all().order_by('-time')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(userId=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """
        API đánh dấu một thông báo đã đọc.
        POST /api/v1/expenses/notifications/{id}/mark_read/
        """
        notification = self.get_object()
        notification.isRead = True
        notification.save()
        return Response({"message": "Đã đánh dấu thông báo là đã đọc."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        """
        API đánh dấu tất cả thông báo của người dùng đã đọc.
        POST /api/v1/expenses/notifications/mark_all_read/
        """
        self.get_queryset().update(isRead=True)
        return Response({"message": "Đã đánh dấu tất cả thông báo là đã đọc."}, status=status.HTTP_200_OK)
