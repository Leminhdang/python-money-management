from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.db.models.functions import TruncDate
from decimal import Decimal
from django.http import HttpResponse

# === Import 2 Module tự xây dựng (OOP) ===
from .phan_tich_chi_tieu import BaoCaoTaiChinh, PhanTichTheoNgay, PhanTichTheoDanhMuc, PhanTichTheoVi
from .xuat_bao_cao import QuanLyXuatBaoCao, XuatJSON, XuatCSV, XuatText

from .models import Category, Wallet, Transaction, Budget, Notification, TransactionType
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
    User thường chỉ xài danh mục của mình, Admin thì quản lý hết.
    """
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_permissions(self):
        # Admin mới đc xóa/sửa danh mục hệ thống
        if self.action in ['destroy', 'update', 'partial_update']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Category.objects.all()
        return Category.objects.filter(userId=self.request.user)

    def perform_create(self, serializer):
        # Gán user hiện tại làm chủ danh mục
        serializer.save(userId=self.request.user)


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý Ví tiền. Mỗi user chỉ thấy ví của mình."""

    queryset = Wallet.objects.all().order_by('name')
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        return Wallet.objects.filter(userId=self.request.user)

    def perform_create(self, serializer):
        serializer.save(userId=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet quản lý Giao dịch Thu/Chi.
    Xử lý tự động: cập nhật số dư Ví, trừ hạn mức Ngân sách, bắn Thông báo.
    """
    queryset = Transaction.objects.all().order_by('-createdAt')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        return Transaction.objects.filter(walletId__userId=self.request.user)

    @db_transaction.atomic
    def perform_create(self, serializer):
        wallet = serializer.validated_data['walletId']

        # Check ví có phải của user ko
        if wallet.userId != self.request.user:
            raise serializers.ValidationError({"walletId": "Ví này ko thuộc của bạn."})

        transaction = serializer.save()

        # Cập nhật số dư ví: chi thì trừ, thu thì cộng
        amount = transaction.amount
        if transaction.type == 'expense':
            wallet.amount -= amount
        else:
            wallet.amount += amount
        wallet.save()

        # Nếu là chi tiêu thì trừ hạn mức ngân sách + bắn cảnh báo
        if transaction.type == 'expense':
            today = timezone.localdate()
            active_budgets = Budget.objects.filter(
                categoryId=transaction.categoryId,
                wallets=wallet,
                fromDate__lte=today,
                toDate__gte=today
            )
            for budget in active_budgets:
                budget.remain -= amount
                budget.save()

                # Bắn thông báo nếu ngân sách hết hoặc âm
                if budget.remain <= 0:
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' dành cho ví '{wallet.name}' đã cạn kiệt hoặc bị âm! Số tiền còn lại: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )
                # Cảnh báo khi còn dưới 10%
                elif budget.remain < (budget.amount * Decimal('0.10')):
                    Notification.objects.create(
                        userId=self.request.user,
                        content=f"Cảnh báo: Ngân sách '{budget.name}' dành cho ví '{wallet.name}' sắp hết! Số tiền còn lại dưới 10%: {budget.remain} đ.",
                        link=f"/api/v1/expenses/budgets/{budget.id}/"
                    )

    @db_transaction.atomic
    def perform_update(self, serializer):
        old_instance = self.get_object()

        # Bước 1: Hoàn tiền lại cho ví cũ
        old_wallet = old_instance.walletId
        if old_instance.type == 'expense':
            old_wallet.amount += old_instance.amount
        else:
            old_wallet.amount -= old_instance.amount
        old_wallet.save()

        # Hoàn hạn mức ngân sách cũ nếu là chi tiêu
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

        # Bước 2: Lưu giao dịch mới
        new_transaction = serializer.save()
        new_wallet = new_transaction.walletId

        if new_wallet.userId != self.request.user:
            raise serializers.ValidationError({"walletId": "Ví mới ko thuộc của bạn."})

        # Áp dụng số dư mới
        new_amount = new_transaction.amount
        if new_transaction.type == 'expense':
            new_wallet.amount -= new_amount
        else:
            new_wallet.amount += new_amount
        new_wallet.save()

        # Trừ hạn mức ngân sách mới (nếu có)
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

        # Hoàn tiền lại ví khi xóa giao dịch
        if instance.type == 'expense':
            wallet.amount += instance.amount
        else:
            wallet.amount -= instance.amount
        wallet.save()

        # Hoàn hạn mức ngân sách
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

    # --- API THỐNG KÊ & BÁO CÁO ---

    @action(detail=False, methods=['get'], url_path='reports/summary')
    def reports_summary(self, request):
        """
        Tổng thu, tổng chi, số dư ròng trong tháng hiện tại.
        GET /api/v1/expenses/transactions/reports/summary/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)

        txs = self.get_queryset().filter(
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        )

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
        Tỷ lệ % chi tiêu theo từng danh mục trong tháng.
        GET /api/v1/expenses/transactions/reports/categories/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)

        expenses = self.get_queryset().filter(
            type='expense',
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        )

        total_expense = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.0')

        if total_expense == 0:
            return Response({"message": "Không có giao dịch chi tiêu nào trong tháng.", "data": []}, status=status.HTTP_200_OK)

        # Gom nhóm theo danh mục, tính tổng tiền
        category_stats = expenses.values('categoryId__name').annotate(
            total_amount=Sum('amount')
        ).order_by('-total_amount')

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
        Biến động thu/chi theo từng ngày trong tháng.
        GET /api/v1/expenses/transactions/reports/daily/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)

        txs = self.get_queryset().filter(
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        )

        daily_stats = txs.annotate(
            date=TruncDate('createdAt')
        ).values('date', 'type').annotate(
            total_amount=Sum('amount')
        ).order_by('date')

        # Gom lại theo ngày cho gọn
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

    # --- 5. API PHÂN TÍCH TỔNG HỢP (Module tự xây dựng: phan_tich_chi_tieu) ---

    @action(detail=False, methods=['get'], url_path='reports/analysis')
    def reports_analysis(self, request):
        """
        API phân tích tổng hợp chi tiêu sử dụng Module OOP tự xây dựng.
        Áp dụng đa hình: cùng 1 danh sách giao dịch, 3 loại phân tích khác nhau.
        GET /api/v1/transactions/reports/analysis/
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)

        # Lấy giao dịch của user trong tháng hiện tại
        txs = self.get_queryset().filter(
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        ).select_related('walletId', 'categoryId')

        # Chuyển đổi QuerySet thành danh sách dict cho module
        ds_giao_dich = []
        for tx in txs:
            ds_giao_dich.append({
                "date": tx.createdAt.strftime('%Y-%m-%d') if tx.createdAt else "",
                "type": tx.type,
                "amount": tx.amount,
                "category": tx.categoryId.name if tx.categoryId else "Không xác định",
                "wallet": tx.walletId.name if tx.walletId else "Không xác định",
            })

        # Sử dụng Module OOP: tạo báo cáo và thêm 3 loại phân tích (đa hình)
        bao_cao = BaoCaoTaiChinh(f"Tháng {today.strftime('%m/%Y')}")
        bao_cao.them_phan_tich(PhanTichTheoNgay())
        bao_cao.them_phan_tich(PhanTichTheoDanhMuc())
        bao_cao.them_phan_tich(PhanTichTheoVi())

        # Gọi đa hình: mỗi loại phân tích tự xử lý theo cách riêng
        bao_cao.chay_phan_tich(ds_giao_dich)

        return Response({
            "month": today.strftime('%m/%Y'),
            "totalTransactions": len(ds_giao_dich),
            "analysis": bao_cao.ket_qua_tong_hop()
        }, status=status.HTTP_200_OK)

    # --- 6. API XUẤT BÁO CÁO ĐA ĐỊNH DẠNG (Module tự xây dựng: xuat_bao_cao) ---

    @action(detail=False, methods=['get'], url_path='reports/export')
    def reports_export(self, request):
        """
        API xuất báo cáo giao dịch ra nhiều định dạng sử dụng Module OOP tự xây dựng.
        Áp dụng đa hình: cùng 1 data, xuất ra JSON / CSV / Text.
        GET /api/v1/transactions/reports/export/?format=json|csv|text
        """
        today = timezone.localdate()
        start_of_month = today.replace(day=1)
        dinh_dang = request.query_params.get('format', 'json').lower()

        # Lấy giao dịch của user trong tháng hiện tại
        txs = self.get_queryset().filter(
            createdAt__date__gte=start_of_month,
            createdAt__date__lte=today
        ).select_related('walletId', 'categoryId')

        ds_giao_dich = []
        for tx in txs:
            ds_giao_dich.append({
                "date": tx.createdAt.strftime('%Y-%m-%d') if tx.createdAt else "",
                "type": tx.type,
                "amount": tx.amount,
                "category": tx.categoryId.name if tx.categoryId else "Không xác định",
                "wallet": tx.walletId.name if tx.walletId else "Không xác định",
                "note": tx.note or "",
            })

        # Sử dụng Module OOP: tạo quản lý xuất và thêm các định dạng
        ql_xuat = QuanLyXuatBaoCao(f"Báo cáo tháng {today.strftime('%m/%Y')}")

        if dinh_dang == 'csv':
            xuat = XuatCSV()
            xuat.xuat(ds_giao_dich)
            response = HttpResponse(xuat.lay_noi_dung(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="bao_cao_{today.strftime("%m_%Y")}.csv"'
            return response

        elif dinh_dang == 'text':
            xuat = XuatText()
            xuat.xuat(ds_giao_dich)
            return HttpResponse(xuat.lay_noi_dung(), content_type='text/plain; charset=utf-8')

        else:
            # Mặc định: trả JSON qua DRF Response
            xuat = XuatJSON()
            xuat.xuat(ds_giao_dich)
            return Response({
                "month": today.strftime('%m/%Y'),
                "format": "JSON",
                "totalTransactions": len(ds_giao_dich),
                "data": ds_giao_dich
            }, status=status.HTTP_200_OK)

    # --- API CHUYỂN KHOẢN ---

    @action(detail=False, methods=['post'], url_path='transfer')
    @db_transaction.atomic
    def transfer(self, request):
        """
        Chuyển khoản nội bộ giữa 2 ví của cùng 1 user.
        POST /api/v1/expenses/transactions/transfer/
        Body: {"fromWalletId": "UUID", "toWalletId": "UUID", "amount": 50000, "note": "..."}
        """
        from_wallet_id = request.data.get('fromWalletId')
        to_wallet_id = request.data.get('toWalletId')
        amount_raw = request.data.get('amount')
        note = request.data.get('note', '')

        # Validate đầu vào
        if not from_wallet_id or not to_wallet_id or not amount_raw:
            return Response(
                {"error": "Vui lòng cung cấp đầy đủ: fromWalletId, toWalletId, amount"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(str(amount_raw))
        except ValueError:
            return Response({"error": "Số tiền ko hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Số tiền phải lớn hơn 0."}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy 2 ví từ DB
        try:
            from_wallet = Wallet.objects.get(id=from_wallet_id, userId=request.user)
            to_wallet = Wallet.objects.get(id=to_wallet_id, userId=request.user)
        except Wallet.DoesNotExist:
            return Response(
                {"error": "Ví ko tồn tại hoặc ko thuộc của bạn."},
                status=status.HTTP_404_NOT_FOUND
            )

        if from_wallet.id == to_wallet.id:
            return Response({"error": "Ko thể chuyển khoản cho chính ví đó."}, status=status.HTTP_400_BAD_REQUEST)

        # Check số dư
        if from_wallet.amount < amount:
            return Response(
                {"error": f"Số dư ví nguồn ko đủ. Hiện tại: {from_wallet.amount} đ."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trừ ví gửi, cộng ví nhận
        from_wallet.amount -= amount
        from_wallet.save()

        to_wallet.amount += amount
        to_wallet.save()

        # Tạo danh mục chuyển khoản nếu chưa có
        category_transfer, _ = Category.objects.get_or_create(
            name="Chuyển khoản nội bộ",
            userId=request.user,
            type=TransactionType.EXPENSE,
            defaults={"parentId": None}
        )

        # Ghi lịch sử: 1 giao dịch chi ở ví gửi, 1 giao dịch thu ở ví nhận
        tx_from = Transaction.objects.create(
            walletId=from_wallet,
            categoryId=category_transfer,
            amount=amount,
            type='expense',
            note=f"Chuyển khoản đến Ví '{to_wallet.name}'. Ghi chú: {note}"
        )

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
    """ViewSet quản lý Hạn mức Ngân sách."""

    queryset = Budget.objects.all().order_by('-fromDate')
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        return Budget.objects.filter(categoryId__userId=self.request.user)

    def perform_create(self, serializer):
        # Khởi tạo remain = amount ban đầu
        amount = serializer.validated_data.get('amount', Decimal('0.0'))
        serializer.save(remain=amount)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet quản lý Thông báo cảnh báo."""

    queryset = Notification.objects.all().order_by('-time')
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    def get_queryset(self):
        return Notification.objects.filter(userId=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        """Đánh dấu 1 thông báo đã đọc."""
        notification = self.get_object()
        notification.isRead = True
        notification.save()
        return Response({"message": "Đã đánh dấu thông báo là đã đọc."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark_all_read')
    def mark_all_read(self, request):
        """Đánh dấu tất cả thông báo đã đọc."""
        self.get_queryset().update(isRead=True)
        return Response({"message": "Đã đánh dấu tất cả thông báo là đã đọc."}, status=status.HTTP_200_OK)
