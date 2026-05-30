# Hệ Thống Web API Quản Lý Thu Chi (Backend Server)

Đây là đồ án kết thúc môn học **Kĩ thuật lập trình Python** tại UIT. Dự án được phát triển dưới dạng **Backend RESTful API Server** (không sử dụng Template giao diện, trả về dữ liệu JSON thuần phục vụ kiểm thử trên Postman). Hệ thống áp dụng chặt chẽ tư duy Lập trình hướng đối tượng (OOP), kiến trúc Model-View-Template (MVT) cải tiến của Django và các chuẩn bảo mật hiện đại.

---

## 🛠️ Công Nghệ Sử Dụng

- **Ngôn ngữ chính:** Python 3.12+
- **Framework:** Django 6.0.5
- **Công cụ API:** Django REST Framework (DRF) 3.17.1
- **Cơ chế xác thực:** JSON Web Token (JWT) qua `djangorestframework-simplejwt`
- **Cơ sở dữ liệu:** SQLite (Lưu trữ tệp cục bộ phục vụ demo gọn nhẹ)

---

## 🚀 Hướng Dẫn Cài Đặt và Khởi Chạy Dự Án

### Bước 1: Kích hoạt môi trường ảo (Virtual Environment)
Mở Terminal ngay tại thư mục chứa đồ án `doan/` và thực hiện:

```bash
# Trên MacOS/Linux
source venv/bin/activate

# Hoặc trên Windows
.\venv\Scripts\activate
```

### Bước 2: Di chuyển vào thư mục dự án và cài đặt thư viện
```bash
cd quan_ly_thu_chi
pip install -r requirements.txt
```

### Bước 3: Đồng bộ và Khởi tạo Cơ sở dữ liệu (Database Migrations)
```bash
python manage.py makemigrations
python manage.py migrate
```

### Bước 4: Tạo tài khoản Admin hệ thống (Superuser)
Tài khoản này dùng để truy cập vào trang Admin `/admin/` và sử dụng các API dành riêng cho Quản trị viên:
```bash
python manage.py createsuperuser
```
*Nhập thông tin: Username, Email, Mật khẩu theo yêu cầu trên màn hình Terminal.*

### Bước 5: Khởi chạy Backend Server
```bash
python manage.py runserver
```
Server sẽ chạy mặc định tại địa chỉ: `http://127.0.0.1:8000/`

---

## 📋 Danh Sách 42 API Endpoints Hệ Thống (`api/v1/`)

Hệ thống được cấu trúc logic, chia làm 2 App con chính:

### 1. Phân hệ Tài khoản & Xác thực (`users`)

| Phương thức | API Endpoint | Chức năng | Phân quyền |
|---|---|---|---|
| `POST` | `/api/v1/users/register/` | Đăng ký tài khoản mới (Mã hóa mật khẩu) | Tự do |
| `POST` | `/api/v1/users/login/` | Đăng nhập hệ thống (Lấy Access & Refresh Token JWT) | Tự do |
| `GET` | `/api/v1/users/profile/` | Xem thông tin cá nhân của User hiện tại | Đã đăng nhập |
| `PUT` | `/api/v1/users/profile/` | Cập nhật toàn bộ thông tin cá nhân | Đã đăng nhập |
| `PATCH` | `/api/v1/users/profile/` | Sửa đổi một phần thông tin cá nhân | Đã đăng nhập |
| `GET` | `/api/v1/users/admin/` | Admin: Danh sách tất cả tài khoản trong hệ thống | Chỉ Admin |
| `POST` | `/api/v1/users/admin/` | Admin: Tạo tài khoản mới trực tiếp | Chỉ Admin |
| `GET` | `/api/v1/users/admin/{id}/` | Admin: Xem thông tin chi tiết tài khoản bất kỳ | Chỉ Admin |
| `PUT` | `/api/v1/users/admin/{id}/` | Admin: Cập nhật thông tin tài khoản | Chỉ Admin |
| `DELETE` | `/api/v1/users/admin/{id}/` | Admin: Xóa vĩnh viễn tài khoản khỏi hệ thống | Chỉ Admin |

### 2. Phân hệ Quản lý Giao dịch & Cảnh báo tài chính (`expenses`)

| Phương thức | API Endpoint | Chức năng | Phân quyền |
|---|---|---|---|
| `GET` | `/api/v1/categories/` | Lấy danh sách danh mục (Tự lồng cây con đệ quy) | Đã đăng nhập |
| `POST` | `/api/v1/categories/` | Tạo danh mục mới | Đã đăng nhập |
| `PUT/PATCH`| `/api/v1/categories/{id}/` | Chỉnh sửa danh mục hệ thống | Chỉ Admin |
| `DELETE` | `/api/v1/categories/{id}/` | Xóa danh mục hệ thống | Chỉ Admin |
| `GET` | `/api/v1/wallets/` | Xem danh sách các Ví cá nhân | Đã đăng nhập |
| `POST` | `/api/v1/wallets/` | Tạo Ví tiền mới | Đã đăng nhập |
| `PUT/PATCH`| `/api/v1/wallets/{id}/` | Cập nhật thông tin Ví (Tên, Loại, Số dư) | Đã đăng nhập |
| `DELETE` | `/api/v1/wallets/{id}/` | Xóa Ví tiền cá nhân | Đã đăng nhập |
| `GET` | `/api/v1/transactions/` | Xem danh sách lịch sử giao dịch Thu/Chi | Đã đăng nhập |
| `POST` | `/api/v1/transactions/` | Tạo giao dịch (**Ví tự động thay đổi, kiểm tra và trừ ngân sách**) | Đã đăng nhập |
| `PUT/PATCH`| `/api/v1/transactions/{id}/` | Sửa giao dịch (**Ví và Ngân sách tự bù trừ chênh lệch số dư**) | Đã đăng nhập |
| `DELETE` | `/api/v1/transactions/{id}/` | Xóa giao dịch (**Ví và Ngân sách tự động hoàn trả số dư**) | Đã đăng nhập |
| `POST` | `/api/v1/transactions/transfer/` | **Chuyển khoản nội bộ giữa 2 Ví của cùng một người dùng** | Đã đăng nhập |
| `GET` | `/api/v1/transactions/reports/summary/`| **Báo cáo tổng quan: Tổng Thu, Tổng Chi, Số dư ròng tháng** | Đã đăng nhập |
| `GET` | `/api/v1/transactions/reports/categories/`| **Báo cáo tỷ lệ % chi tiêu theo danh mục (Biểu đồ tròn)** | Đã đăng nhập |
| `GET` | `/api/v1/transactions/reports/daily/` | **Báo cáo dòng tiền biến động theo ngày (Biểu đồ cột)** | Đã đăng nhập |
| `GET/POST` | `/api/v1/budgets/` | Thiết lập ngân sách (Tự động gán remain = amount) | Đã đăng nhập |
| `PUT/DELETE`| `/api/v1/budgets/{id}/` | Cập nhật / Xóa ngân sách | Đã đăng nhập |
| `GET` | `/api/v1/notifications/` | Xem danh sách các cảnh báo an toàn ngân sách | Đã đăng nhập |
| `POST` | `/api/v1/notifications/{id}/mark_read/`| Đánh dấu thông báo cụ thể là đã đọc | Đã đăng nhập |
| `POST` | `/api/v1/notifications/mark_all_read/`| Đánh dấu tất cả thông báo là đã đọc | Đã đăng nhập |

---

## 🎯 Kịch Bản Demo Test Hệ Thống Trên Postman

Hãy thực hiện tuần tự theo kịch bản 10 bước dưới đây để trình diễn trọn vẹn sức mạnh xử lý nghiệp vụ tự động hóa và kiến trúc OOP của đồ án trước Hội đồng/Giảng viên chấm thi.

### BƯỚC 1: Đăng ký tài khoản mới (`Register`)
- **API:** `POST http://127.0.0.1:8000/api/v1/users/register/`
- **Body (JSON):**
```json
{
  "username": "student_uit",
  "email": "student@uit.edu.vn",
  "password": "SecretPassword123",
  "passwordConfirm": "SecretPassword123",
  "name": "Nguyễn Văn Sinh Viên",
  "birthday": "2004-05-15",
  "phoneNumber": "0987654321",
  "address": "UIT, Thủ Đức, TP.HCM"
}
```
- **Kết quả mong đợi:** Mã HTTP `201 Created`. JSON trả về chứa ID của User dạng UUID và password đã được băm mã hóa một chiều.

---

### BƯỚC 2: Đăng nhập nhận Token xác thực (`Login`)
- **API:** `POST http://127.0.0.1:8000/api/v1/users/login/`
- **Body (JSON) - Đăng nhập bằng Email:**
```json
{
  "usernameOrEmail": "student@uit.edu.vn",
  "password": "SecretPassword123"
}
```
- **Kết quả mong đợi:** Mã HTTP `200 OK`. JSON trả về chứa Token:
```json
{
  "user": { ... },
  "access": "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```
> ⚠️ **HƯỚNG DẪN POSTMAN:** Copy giá trị chuỗi dài trong khóa `"access"`. Tại Postman, vào tab **Authorization** -> chọn Type **Bearer Token** -> Dán chuỗi này vào ô **Token** để thực hiện tất cả các bước tiếp theo.

---

### BƯỚC 3: Tạo Ví tiền nguồn (`Wallet 1`)
- **API:** `POST http://127.0.0.1:8000/api/v1/wallets/`
- **Body (JSON):**
```json
{
  "name": "Ví ATM Techcombank",
  "type": "ATM",
  "amount": "5000000.00"
}
```
- **Kết quả mong đợi:** Trả về thông tin Ví mới tạo với số dư ban đầu là **5.000.000 đ**. Lưu lại `id` (dạng UUID) của ví này làm `VÍ_A`.

---

### BƯỚC 4: Tạo Ví tiền đích (`Wallet 2`)
- **API:** `POST http://127.0.0.1:8000/api/v1/wallets/`
- **Body (JSON):**
```json
{
  "name": "Ví Momo Tiết Kiệm",
  "type": "Ví điện tử",
  "amount": "1000000.00"
}
```
- **Kết quả mong đợi:** Trả về Ví Momo có số dư **1.000.000 đ**. Lưu lại `id` của ví này làm `VÍ_B`.

---

### BƯỚC 5: Tạo Danh mục chi tiêu (`Category`)
- **API:** `POST http://127.0.0.1:8000/api/v1/categories/`
- **Body (JSON):**
```json
{
  "name": "Ăn uống hàng ngày",
  "type": "expense",
  "parentId": null
}
```
- **Kết quả mong đợi:** Trả về danh mục thuộc loại Chi tiêu (`expense`). Lưu lại `id` làm `DANH_MỤC_X`.

---

### BƯỚC 6: Tạo Ngân sách giới hạn chi tiêu (`Budget`)
Chúng ta sẽ cài đặt một Ngân sách ăn uống với hạn mức là 1.000.000 đ.
- **API:** `POST http://127.0.0.1:8000/api/v1/budgets/`
- **Body (JSON):** *(Thay `DANH_MỤC_X` và `VÍ_A` bằng UUID thực tế đã lưu ở trên)*
```json
{
  "name": "Ngân Sách Ăn Uống Tháng 5",
  "categoryId": "DANH_MỤC_X",
  "amount": "1000000.00",
  "loop": false,
  "fromDate": "2026-05-01",
  "toDate": "2026-05-31",
  "note": "Hạn mức tối đa cho việc ăn uống",
  "wallets": [
    "VÍ_A"
  ]
}
```
- **Kết quả mong đợi:** Hệ thống tự động gán số dư ngân sách còn lại `"remain": "1000000.00"`.

---

### BƯỚC 7: Thực hiện Chi tiêu & Trình diễn Tự động hóa nghiệp vụ (BƯỚC QUAN TRỌNG NHẤT 🌟)
Tạo giao dịch Chi tiêu ăn uống trị giá **950.000 đ** bằng `VÍ_A` để kiểm tra logic trừ tiền ví, trừ hạn mức ngân sách và bắn thông báo cảnh báo sớm (Vì số dư ngân sách còn 50.000 đ < 10%).

- **API:** `POST http://127.0.0.1:8000/api/v1/transactions/`
- **Body (JSON):**
```json
{
  "walletId": "VÍ_A",
  "categoryId": "DANH_MỤC_X",
  "amount": "950000.00",
  "type": "expense",
  "note": "Đi ăn lẩu buffet UIT với lớp"
}
```
- **Logic tự động hóa xảy ra ngầm trong DB:**
  1. Số dư `VÍ_A` tự động giảm từ 5.000.000 đ xuống **4.050.000 đ**.
  2. Số dư ngân sách còn lại `remain` tự động trừ đi 950.000 đ, chỉ còn **50.000 đ**.
  3. Do số dư ngân sách 50.000 đ nhỏ hơn 10% hạn mức ban đầu (100.000 đ), hệ thống **tự tạo bản ghi Notification cảnh báo**.
- **Cách chứng minh với giảng viên:**
  - Gọi lại API xem Ví tiền (`GET /api/v1/wallets/`) -> Số dư đã đổi thành 4.050.000 đ.
  - Gọi lại API xem Ngân sách (`GET /api/v1/budgets/`) -> Số tiền còn lại `remain` chỉ còn 50.000 đ.
  - Gọi API xem Cảnh báo (`GET /api/v1/notifications/`) -> Nhận về thông báo cảnh báo vượt ngưỡng!

---

### BƯỚC 8: Chuyển khoản nội bộ giữa 2 ví (`Transfer`)
Chuyển khoản 500.000 đ từ `VÍ_A` sang `VÍ_B`.
- **API:** `POST http://127.0.0.1:8000/api/v1/transactions/transfer/`
- **Body (JSON):**
```json
{
  "fromWalletId": "VÍ_A",
  "toWalletId": "VÍ_B",
  "amount": "500000.00",
  "note": "Chuyển tiền ăn uống từ thẻ ATM sang Momo"
}
```
- **Kết quả mong đợi:** Mã HTTP `200 OK`. 
  - `VÍ_A` (ATM) tự trừ 500.000 đ, số dư còn lại: **3.550.000 đ**.
  - `VÍ_B` (Momo) tự cộng 500.000 đ, số dư mới: **1.500.000 đ**.
  - Tự sinh ra 2 giao dịch Thu và Chi làm lịch sử đối chiếu chuyển khoản.

---

### BƯỚC 9: Kiểm tra API Thống kê chuyên sâu phục vụ vẽ Biểu đồ (`Reports`)
- **API 1 (Tổng quan tháng):** `GET http://127.0.0.1:8000/api/v1/transactions/reports/summary/`
  - *Dữ liệu trả về:* `"totalIncome": 500000.00` (từ giao dịch chuyển khoản Momo nhận), `"totalExpense": 1450000.00` (giao dịch ăn uống 950k + chuyển khoản ví ATM 500k), số dư ròng âm trong tháng.
- **API 2 (Phân phối danh mục):** `GET http://127.0.0.1:8000/api/v1/transactions/reports/categories/`
  - *Dữ liệu trả về:* Tỷ lệ % chi tiêu của từng danh mục trong tháng (Ví dụ: "Ăn uống hàng ngày": 65.52%, "Chuyển khoản nội bộ": 34.48%).
- **API 3 (Biến động theo ngày):** `GET http://127.0.0.1:8000/api/v1/transactions/reports/daily/`
  - *Dữ liệu trả về:* Mảng danh sách dòng tiền (Thu vs Chi) theo các ngày của tháng hiện tại.

---

### BƯỚC 10: Xóa giao dịch để hoàn trả lại trạng thái (Kiểm thử tính bù trừ)
Nếu chúng ta xóa giao dịch ăn uống buffet 950.000 đ ở Bước 7:
- **API:** `DELETE http://127.0.0.1:8000/api/v1/transactions/{ID_GIAO_DỊCH_950K}/`
- **Kết quả mong đợi:** 
  - `VÍ_A` tự động được hoàn tiền 950.000 đ, tăng lại từ 3.550.000 đ lên **4.500.000 đ**.
  - Số dư ngân sách `remain` cũng tự động được hoàn trả, tăng lại từ 50.000 đ lên **1.000.000 đ** như lúc đầu.
