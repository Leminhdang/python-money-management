"""
Module Phân Tích Chi Tiêu - Tự xây dựng theo mô hình OOP
Áp dụng: Abstract Class, Kế thừa, Đa hình (Polymorphism)

Cấu trúc:
    ABCPhanTich (ABC)           ← Lớp trừu tượng gốc
      ├── PhanTichTheoNgay      ← Phân tích tổng thu/chi theo từng ngày
      ├── PhanTichTheoDanhMuc   ← Phân tích tỷ lệ % chi tiêu theo danh mục
      └── PhanTichTheoVi        ← Phân tích số dư và giao dịch theo từng ví

    BaoCaoTaiChinh              ← Lớp quản lý: chứa danh sách và gọi đa hình
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from collections import defaultdict


class ABCPhanTich(ABC):
    """Lớp trừu tượng định nghĩa giao diện chung cho mọi loại phân tích."""

    def __init__(self, ten_phan_tich: str):
        self._ten = ten_phan_tich
        self._ket_qua = None

    @abstractmethod
    def phan_tich(self, ds_giao_dich: list) -> dict:
        """Phân tích danh sách giao dịch và trả về kết quả dạng dict."""
        pass

    def lay_ten(self) -> str:
        return self._ten

    def lay_ket_qua(self) -> dict:
        return self._ket_qua

    def __str__(self):
        return f"[{self._ten}] Kết quả: {self._ket_qua}"


class PhanTichTheoNgay(ABCPhanTich):
    """Phân tích tổng thu, tổng chi theo từng ngày."""

    def __init__(self):
        super().__init__("Phân tích theo ngày")

    def phan_tich(self, ds_giao_dich: list) -> dict:
        """
        Input: danh sách dict giao dịch [{"date": "2025-06-01", "type": "expense", "amount": 50000}, ...]
        Output: {"2025-06-01": {"thu": 0, "chi": 50000}, ...}
        """
        theo_ngay = defaultdict(lambda: {"thu": Decimal("0"), "chi": Decimal("0")})

        for gd in ds_giao_dich:
            ngay = str(gd.get("date", "Không xác định"))
            so_tien = Decimal(str(gd.get("amount", 0)))
            loai = gd.get("type", "")

            if loai == "income":
                theo_ngay[ngay]["thu"] += so_tien
            elif loai == "expense":
                theo_ngay[ngay]["chi"] += so_tien

        # Sắp xếp theo ngày
        self._ket_qua = dict(sorted(theo_ngay.items()))
        return self._ket_qua


class PhanTichTheoDanhMuc(ABCPhanTich):
    """Phân tích tỷ lệ phần trăm chi tiêu theo từng danh mục."""

    def __init__(self):
        super().__init__("Phân tích theo danh mục")

    def phan_tich(self, ds_giao_dich: list) -> dict:
        """
        Input: danh sách dict giao dịch [{"category": "Ăn uống", "type": "expense", "amount": 50000}, ...]
        Output: {"Ăn uống": {"so_tien": 50000, "ty_le": 100.0}, ...}
        """
        theo_dm = defaultdict(lambda: Decimal("0"))
        tong_chi = Decimal("0")

        for gd in ds_giao_dich:
            if gd.get("type") == "expense":
                danh_muc = gd.get("category", "Không xác định")
                so_tien = Decimal(str(gd.get("amount", 0)))
                theo_dm[danh_muc] += so_tien
                tong_chi += so_tien

        # Tính tỷ lệ phần trăm
        ket_qua = {}
        for dm, tien in sorted(theo_dm.items(), key=lambda x: x[1], reverse=True):
            ty_le = round((tien / tong_chi) * 100, 2) if tong_chi > 0 else Decimal("0")
            ket_qua[dm] = {"so_tien": tien, "ty_le": float(ty_le)}

        self._ket_qua = {"tong_chi": tong_chi, "chi_tiet": ket_qua}
        return self._ket_qua


class PhanTichTheoVi(ABCPhanTich):
    """Phân tích tổng thu, tổng chi và số giao dịch theo từng ví."""

    def __init__(self):
        super().__init__("Phân tích theo ví")

    def phan_tich(self, ds_giao_dich: list) -> dict:
        """
        Input: danh sách dict giao dịch [{"wallet": "Techcombank", "type": "expense", "amount": 50000}, ...]
        Output: {"Techcombank": {"thu": 0, "chi": 50000, "so_giao_dich": 1}, ...}
        """
        theo_vi = defaultdict(lambda: {"thu": Decimal("0"), "chi": Decimal("0"), "so_giao_dich": 0})

        for gd in ds_giao_dich:
            vi = gd.get("wallet", "Không xác định")
            so_tien = Decimal(str(gd.get("amount", 0)))
            loai = gd.get("type", "")

            theo_vi[vi]["so_giao_dich"] += 1
            if loai == "income":
                theo_vi[vi]["thu"] += so_tien
            elif loai == "expense":
                theo_vi[vi]["chi"] += so_tien

        self._ket_qua = dict(theo_vi)
        return self._ket_qua


class BaoCaoTaiChinh:
    """
    Lớp quản lý trung tâm — tương tự class Luong trong mẫu giáo viên.
    Chứa danh sách các đối tượng phân tích và gọi phan_tich() đa hình trên tất cả.
    """

    def __init__(self, tieu_de: str):
        self._tieu_de = tieu_de
        self.__ds_phan_tich = []

    def them_phan_tich(self, phan_tich: ABCPhanTich):
        """Thêm một loại phân tích vào danh sách."""
        self.__ds_phan_tich.append(phan_tich)

    def chay_phan_tich(self, ds_giao_dich: list):
        """Gọi phan_tich() đa hình trên toàn bộ danh sách — giống tinh_luong_ht() của thầy."""
        list(map(lambda pt: pt.phan_tich(ds_giao_dich), self.__ds_phan_tich))

    def ds_phan_tich(self):
        return self.__ds_phan_tich

    def ket_qua_tong_hop(self) -> dict:
        """Trả về kết quả tổng hợp từ tất cả các loại phân tích."""
        return {pt.lay_ten(): pt.lay_ket_qua() for pt in self.__ds_phan_tich}

    def __str__(self):
        return f"Báo cáo: {self._tieu_de} — {len(self.__ds_phan_tich)} phân tích"


# ============================================================
# Demo chạy độc lập (giống if __name__ == "__main__" của thầy)
# ============================================================
if __name__ == "__main__":
    # Dữ liệu mẫu
    du_lieu = [
        {"date": "2025-06-01", "type": "expense", "amount": 950000, "category": "Ăn uống", "wallet": "Techcombank"},
        {"date": "2025-06-01", "type": "income", "amount": 5000000, "category": "Lương", "wallet": "Techcombank"},
        {"date": "2025-06-02", "type": "expense", "amount": 200000, "category": "Di chuyển", "wallet": "Momo"},
        {"date": "2025-06-02", "type": "expense", "amount": 150000, "category": "Ăn uống", "wallet": "Momo"},
    ]

    # Tạo báo cáo và thêm các loại phân tích
    bao_cao = BaoCaoTaiChinh("Tháng 6/2025")
    bao_cao.them_phan_tich(PhanTichTheoNgay())
    bao_cao.them_phan_tich(PhanTichTheoDanhMuc())
    bao_cao.them_phan_tich(PhanTichTheoVi())

    # Chạy phân tích đa hình
    bao_cao.chay_phan_tich(du_lieu)

    # In kết quả
    print(bao_cao)
    for pt in bao_cao.ds_phan_tich():
        print(pt)
