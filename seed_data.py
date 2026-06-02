"""
Script tạo dữ liệu mẫu (Mock Data) để demo đồ án.
Chạy bằng: python manage.py shell < seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quan_ly_thu_chi.settings')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from users.models import User
from expenses.models import Category, Wallet, Transaction, Budget, Budget_Wallets, Notification

# ============================================================
# 0. Xóa dữ liệu cũ (nếu có)
# ============================================================
print("🗑️  Xóa dữ liệu cũ...")
Notification.objects.all().delete()
Transaction.objects.all().delete()
Budget_Wallets.objects.all().delete()
Budget.objects.all().delete()
Category.objects.all().delete()
Wallet.objects.all().delete()
User.objects.filter(is_superuser=False).delete()

# ============================================================
# 1. Tạo User
# ============================================================
print("👤 Tạo tài khoản người dùng...")
user = User.objects.create_user(
    username='leminhdang',
    email='leminhdang@gmail.com',
    password='123123123a',
    name='Lê Minh Đăng',
    phoneNumber='0901234567',
    address='TP. Hồ Chí Minh'
)

user2 = User.objects.create_user(
    username='quoctung',
    email='quoctung@gmail.com',
    password='123123123a',
    name='Quốc Tùng',
    phoneNumber='0912345678',
    address='TP. Hồ Chí Minh'
)

# Tạo admin nếu chưa có
if not User.objects.filter(is_superuser=True).exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@gmail.com',
        password='admin123',
        name='Quản trị viên'
    )
    print(f"   ✅ Admin: admin@gmail.com / admin123")

print(f"   ✅ User 1: leminhdang@gmail.com / 123123123a")
print(f"   ✅ User 2: quoctung@gmail.com / 123123123a")

# ============================================================
# 2. Tạo Ví
# ============================================================
print("💳 Tạo ví tiền...")
# Ví của Lê Minh Đăng
vi_tcb = Wallet.objects.create(userId=user, name="ATM Techcombank", type="Ngân hàng", amount=Decimal("5000000"))
vi_momo = Wallet.objects.create(userId=user, name="Ví Momo", type="Ví điện tử", amount=Decimal("1000000"))
vi_tienmat = Wallet.objects.create(userId=user, name="Tiền mặt", type="Tiền mặt", amount=Decimal("2000000"))
# Ví của Quốc Tùng
vi2_vcb = Wallet.objects.create(userId=user2, name="ATM Vietcombank", type="Ngân hàng", amount=Decimal("8000000"))
vi2_zalopay = Wallet.objects.create(userId=user2, name="ZaloPay", type="Ví điện tử", amount=Decimal("1500000"))
print(f"   ✅ 5 ví: Đăng (3 ví), Tùng (2 ví)")

# ============================================================
# 3. Tạo Danh mục
# ============================================================
print("📂 Tạo danh mục...")
# Danh mục chi tiêu
dm_anuong = Category.objects.create(userId=user, name="Ăn uống hàng ngày", type="expense")
dm_dichuyen = Category.objects.create(userId=user, name="Di chuyển", type="expense")
dm_giaitri = Category.objects.create(userId=user, name="Giải trí", type="expense")
dm_hocphi = Category.objects.create(userId=user, name="Học phí & Sách vở", type="expense")
dm_muasam = Category.objects.create(userId=user, name="Mua sắm", type="expense")

# Danh mục con (đệ quy)
dm_cafe = Category.objects.create(userId=user, name="Cà phê", type="expense", parentId=dm_anuong)
dm_com = Category.objects.create(userId=user, name="Cơm trưa/tối", type="expense", parentId=dm_anuong)

# Danh mục thu nhập
dm_luong = Category.objects.create(userId=user, name="Lương tháng", type="income")
dm_thuong = Category.objects.create(userId=user, name="Thưởng / Phụ cấp", type="income")
dm_lamthem = Category.objects.create(userId=user, name="Làm thêm freelance", type="income")
print(f"   ✅ 10 danh mục (7 chi + 3 thu, có danh mục con đệ quy)")

# ============================================================
# 4. Tạo Ngân sách
# ============================================================
print("📊 Tạo ngân sách...")
today = date.today()
start_month = today.replace(day=1)
end_month = (start_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

ns_anuong = Budget.objects.create(
    name="Ngân sách ăn uống tháng",
    categoryId=dm_anuong,
    amount=Decimal("2000000"),
    remain=Decimal("2000000"),
    loop=True,
    fromDate=start_month,
    toDate=end_month,
    note="Hạn mức chi tiêu ăn uống trong tháng"
)
Budget_Wallets.objects.create(budgetId=ns_anuong, walletId=vi_tcb)
Budget_Wallets.objects.create(budgetId=ns_anuong, walletId=vi_tienmat)

ns_giaitri = Budget.objects.create(
    name="Ngân sách giải trí tháng",
    categoryId=dm_giaitri,
    amount=Decimal("500000"),
    remain=Decimal("500000"),
    loop=True,
    fromDate=start_month,
    toDate=end_month,
    note="Hạn mức chi tiêu giải trí"
)
Budget_Wallets.objects.create(budgetId=ns_giaitri, walletId=vi_momo)
print(f"   ✅ 2 ngân sách: Ăn uống (2tr), Giải trí (500k)")

# ============================================================
# 5. Tạo Giao dịch (phân bố trong tháng)
# ============================================================
print("💰 Tạo giao dịch mẫu...")

giao_dich_mau = [
    # Thu nhập
    {"wallet": vi_tcb, "category": dm_luong, "amount": "8500000", "type": "income", "note": "Lương tháng từ công ty ABC", "days_ago": 25},
    {"wallet": vi_momo, "category": dm_lamthem, "amount": "2000000", "type": "income", "note": "Freelance thiết kế UI/UX", "days_ago": 20},
    {"wallet": vi_tcb, "category": dm_thuong, "amount": "1000000", "type": "income", "note": "Thưởng KPI quý 2", "days_ago": 15},
    # Chi tiêu - Ăn uống
    {"wallet": vi_tcb, "category": dm_anuong, "amount": "950000", "type": "expense", "note": "Buffet lẩu UIT cùng bạn bè", "days_ago": 22},
    {"wallet": vi_tienmat, "category": dm_com, "amount": "35000", "type": "expense", "note": "Cơm trưa căn tin", "days_ago": 21},
    {"wallet": vi_tienmat, "category": dm_com, "amount": "40000", "type": "expense", "note": "Cơm tối Bách Hóa Xanh", "days_ago": 20},
    {"wallet": vi_tienmat, "category": dm_cafe, "amount": "29000", "type": "expense", "note": "Highlands Coffee", "days_ago": 19},
    {"wallet": vi_tcb, "category": dm_anuong, "amount": "120000", "type": "expense", "note": "Grab Food - Gà rán", "days_ago": 18},
    {"wallet": vi_tienmat, "category": dm_com, "amount": "35000", "type": "expense", "note": "Cơm trưa căn tin", "days_ago": 15},
    {"wallet": vi_tienmat, "category": dm_cafe, "amount": "45000", "type": "expense", "note": "The Coffee House", "days_ago": 12},
    {"wallet": vi_tcb, "category": dm_anuong, "amount": "180000", "type": "expense", "note": "Pizza 4P's sinh nhật bạn", "days_ago": 8},
    {"wallet": vi_tienmat, "category": dm_com, "amount": "38000", "type": "expense", "note": "Bún bò Huế", "days_ago": 5},
    {"wallet": vi_tienmat, "category": dm_cafe, "amount": "35000", "type": "expense", "note": "Phúc Long trà sữa", "days_ago": 3},
    {"wallet": vi_tcb, "category": dm_anuong, "amount": "250000", "type": "expense", "note": "Nhậu cuối tuần", "days_ago": 1},
    # Chi tiêu - Di chuyển
    {"wallet": vi_momo, "category": dm_dichuyen, "amount": "45000", "type": "expense", "note": "Grab Bike đi học", "days_ago": 21},
    {"wallet": vi_momo, "category": dm_dichuyen, "amount": "32000", "type": "expense", "note": "Grab Bike về nhà", "days_ago": 21},
    {"wallet": vi_momo, "category": dm_dichuyen, "amount": "55000", "type": "expense", "note": "Grab Car đi phỏng vấn", "days_ago": 14},
    {"wallet": vi_momo, "category": dm_dichuyen, "amount": "25000", "type": "expense", "note": "Xe buýt", "days_ago": 7},
    # Chi tiêu - Giải trí
    {"wallet": vi_momo, "category": dm_giaitri, "amount": "120000", "type": "expense", "note": "Vé xem phim CGV", "days_ago": 16},
    {"wallet": vi_momo, "category": dm_giaitri, "amount": "79000", "type": "expense", "note": "Netflix Premium tháng", "days_ago": 10},
    {"wallet": vi_momo, "category": dm_giaitri, "amount": "150000", "type": "expense", "note": "Quán billiards cùng nhóm", "days_ago": 4},
    # Chi tiêu - Học phí
    {"wallet": vi_tcb, "category": dm_hocphi, "amount": "850000", "type": "expense", "note": "Mua sách Lập trình Python", "days_ago": 23},
    # Chi tiêu - Mua sắm
    {"wallet": vi_tcb, "category": dm_muasam, "amount": "350000", "type": "expense", "note": "Áo thun Uniqlo", "days_ago": 11},
    {"wallet": vi_momo, "category": dm_muasam, "amount": "199000", "type": "expense", "note": "Tai nghe Bluetooth Shopee", "days_ago": 6},
]

count = 0
for gd in giao_dich_mau:
    ngay_tao = timezone.now() - timedelta(days=gd["days_ago"])
    tx = Transaction.objects.create(
        walletId=gd["wallet"],
        categoryId=gd["category"],
        amount=Decimal(gd["amount"]),
        type=gd["type"],
        note=gd["note"],
    )
    # Cập nhật ngày tạo thủ công
    Transaction.objects.filter(pk=tx.pk).update(createdAt=ngay_tao)

    # Cập nhật số dư ví
    if gd["type"] == "expense":
        gd["wallet"].amount -= Decimal(gd["amount"])
    else:
        gd["wallet"].amount += Decimal(gd["amount"])
    gd["wallet"].save()

    # Cập nhật ngân sách nếu là chi tiêu
    if gd["type"] == "expense":
        active_budgets = Budget.objects.filter(
            categoryId=gd["category"],
            wallets=gd["wallet"],
            fromDate__lte=today,
            toDate__gte=today
        )
        for budget in active_budgets:
            budget.remain -= Decimal(gd["amount"])
            budget.save()

            # Sinh cảnh báo nếu cần
            if budget.remain <= 0:
                Notification.objects.create(
                    userId=user,
                    content=f"⚠️ Cảnh báo: Ngân sách '{budget.name}' đã cạn kiệt! Còn lại: {budget.remain} đ.",
                    link=f"/api/v1/budgets/{budget.id}/"
                )
            elif budget.remain < (budget.amount * Decimal('0.10')):
                Notification.objects.create(
                    userId=user,
                    content=f"⚠️ Cảnh báo: Ngân sách '{budget.name}' sắp hết! Còn dưới 10%: {budget.remain} đ.",
                    link=f"/api/v1/budgets/{budget.id}/"
                )
    count += 1

print(f"   ✅ {count} giao dịch Lê Minh Đăng (3 thu + 21 chi)")

# ============================================================
# 5b. Tạo Giao dịch cho Quốc Tùng
# ============================================================
print("💰 Tạo giao dịch mẫu cho Quốc Tùng...")

# Danh mục riêng cho Quốc Tùng
dm2_anuong = Category.objects.create(userId=user2, name="Ăn uống", type="expense")
dm2_dichuyen = Category.objects.create(userId=user2, name="Di chuyển", type="expense")
dm2_luong = Category.objects.create(userId=user2, name="Lương", type="income")

giao_dich_tung = [
    {"wallet": vi2_vcb, "category": dm2_luong, "amount": "12000000", "type": "income", "note": "Lương tháng công ty XYZ", "days_ago": 25},
    {"wallet": vi2_vcb, "category": dm2_anuong, "amount": "85000", "type": "expense", "note": "Cơm văn phòng", "days_ago": 20},
    {"wallet": vi2_zalopay, "category": dm2_dichuyen, "amount": "38000", "type": "expense", "note": "Grab Bike", "days_ago": 18},
    {"wallet": vi2_vcb, "category": dm2_anuong, "amount": "120000", "type": "expense", "note": "Ăn tối cùng đồng nghiệp", "days_ago": 12},
    {"wallet": vi2_zalopay, "category": dm2_anuong, "amount": "45000", "type": "expense", "note": "Trà sữa Gong Cha", "days_ago": 5},
    {"wallet": vi2_vcb, "category": dm2_dichuyen, "amount": "60000", "type": "expense", "note": "Grab Car đi họp", "days_ago": 3},
]

count2 = 0
for gd in giao_dich_tung:
    ngay_tao = timezone.now() - timedelta(days=gd["days_ago"])
    tx = Transaction.objects.create(
        walletId=gd["wallet"],
        categoryId=gd["category"],
        amount=Decimal(gd["amount"]),
        type=gd["type"],
        note=gd["note"],
    )
    Transaction.objects.filter(pk=tx.pk).update(createdAt=ngay_tao)
    if gd["type"] == "expense":
        gd["wallet"].amount -= Decimal(gd["amount"])
    else:
        gd["wallet"].amount += Decimal(gd["amount"])
    gd["wallet"].save()
    count2 += 1

print(f"   ✅ {count2} giao dịch Quốc Tùng (1 thu + 5 chi)")

# ============================================================
# 6. Tổng kết
# ============================================================
print("\n" + "=" * 50)
print("🎉 TẠO DỮ LIỆU MẪU HOÀN TẤT!")
print("=" * 50)
print(f"   👤 User: {User.objects.count()}")
print(f"   💳 Ví: {Wallet.objects.count()}")
print(f"   📂 Danh mục: {Category.objects.count()}")
print(f"   💰 Giao dịch: {Transaction.objects.count()}")
print(f"   📊 Ngân sách: {Budget.objects.count()}")
print(f"   🔔 Thông báo: {Notification.objects.count()}")
print(f"\n   === Lê Minh Đăng ===")
for vi in Wallet.objects.filter(userId=user):
    print(f"     - {vi.name}: {vi.amount:,.0f} đ")
print(f"\n   === Quốc Tùng ===")
for vi in Wallet.objects.filter(userId=user2):
    print(f"     - {vi.name}: {vi.amount:,.0f} đ")
print(f"\n   Ngân sách còn lại:")
for ns in Budget.objects.filter(categoryId__userId=user):
    print(f"     - {ns.name}: {ns.remain:,.0f} / {ns.amount:,.0f} đ")
print(f"\n🔑 Đăng nhập:")
print(f"   User 1: {{\"usernameOrEmail\": \"leminhdang@gmail.com\", \"password\": \"123123123a\"}}")
print(f"   User 2: {{\"usernameOrEmail\": \"quoctung@gmail.com\", \"password\": \"123123123a\"}}")
