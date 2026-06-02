"""
Module Xuất Báo Cáo - Tự xây dựng theo mô hình OOP
Áp dụng: Abstract Class, Kế thừa, Đa hình (Polymorphism)

Cấu trúc:
    ABCXuatBaoCao (ABC)         ← Lớp trừu tượng gốc
      ├── XuatJSON              ← Xuất dữ liệu dạng JSON string
      ├── XuatCSV               ← Xuất dữ liệu dạng CSV string
      └── XuatText              ← Xuất dữ liệu dạng bảng văn bản

    QuanLyXuatBaoCao            ← Lớp quản lý: chứa danh sách và gọi đa hình
"""

from abc import ABC, abstractmethod
from decimal import Decimal
import json
import io
import csv


class ABCXuatBaoCao(ABC):
    """Lớp trừu tượng định nghĩa giao diện chung cho mọi định dạng xuất."""

    def __init__(self, ten_dinh_dang: str):
        self._ten = ten_dinh_dang
        self._noi_dung = None

    @abstractmethod
    def xuat(self, ds_giao_dich: list) -> str:
        """Xuất danh sách giao dịch ra định dạng tương ứng, trả về chuỗi."""
        pass

    def lay_ten(self) -> str:
        return self._ten

    def lay_noi_dung(self) -> str:
        return self._noi_dung

    def __str__(self):
        return f"[{self._ten}] Đã xuất {len(self._noi_dung) if self._noi_dung else 0} ký tự"


class DecimalEncoder(json.JSONEncoder):
    """Hỗ trợ JSON encode cho kiểu Decimal."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class XuatJSON(ABCXuatBaoCao):
    """Xuất báo cáo dưới dạng chuỗi JSON."""

    def __init__(self):
        super().__init__("JSON")

    def xuat(self, ds_giao_dich: list) -> str:
        """
        Input: [{"date": "2025-06-01", "type": "expense", "amount": 50000, ...}, ...]
        Output: chuỗi JSON đẹp có thụt dòng
        """
        self._noi_dung = json.dumps(
            ds_giao_dich,
            ensure_ascii=False,
            indent=2,
            cls=DecimalEncoder
        )
        return self._noi_dung


class XuatCSV(ABCXuatBaoCao):
    """Xuất báo cáo dưới dạng chuỗi CSV."""

    def __init__(self):
        super().__init__("CSV")

    def xuat(self, ds_giao_dich: list) -> str:
        """
        Input: [{"date": "2025-06-01", "type": "expense", "amount": 50000, ...}, ...]
        Output: chuỗi CSV có header
        """
        if not ds_giao_dich:
            self._noi_dung = ""
            return self._noi_dung

        output = io.StringIO()
        # Lấy tên cột từ dict đầu tiên
        ten_cot = list(ds_giao_dich[0].keys())
        writer = csv.DictWriter(output, fieldnames=ten_cot)
        writer.writeheader()

        for gd in ds_giao_dich:
            # Chuyển Decimal sang float cho CSV
            dong = {}
            for k, v in gd.items():
                dong[k] = float(v) if isinstance(v, Decimal) else v
            writer.writerow(dong)

        self._noi_dung = output.getvalue()
        output.close()
        return self._noi_dung


class XuatText(ABCXuatBaoCao):
    """Xuất báo cáo dưới dạng bảng văn bản (text table)."""

    def __init__(self):
        super().__init__("Text")

    def xuat(self, ds_giao_dich: list) -> str:
        """
        Input: [{"date": "2025-06-01", "type": "expense", "amount": 50000, ...}, ...]
        Output: bảng văn bản có đường kẻ
        """
        if not ds_giao_dich:
            self._noi_dung = "(Không có dữ liệu)"
            return self._noi_dung

        ten_cot = list(ds_giao_dich[0].keys())

        # Tính độ rộng mỗi cột
        do_rong = {}
        for col in ten_cot:
            do_rong[col] = max(
                len(str(col)),
                max(len(str(gd.get(col, ""))) for gd in ds_giao_dich)
            )

        # Tạo đường kẻ ngang
        duong_ke = "+" + "+".join("-" * (do_rong[col] + 2) for col in ten_cot) + "+"

        # Tạo header
        header = "|" + "|".join(f" {col:^{do_rong[col]}} " for col in ten_cot) + "|"

        # Tạo các dòng dữ liệu
        cac_dong = []
        for gd in ds_giao_dich:
            dong = "|" + "|".join(
                f" {str(gd.get(col, '')):>{do_rong[col]}} " for col in ten_cot
            ) + "|"
            cac_dong.append(dong)

        # Ghép bảng
        bang = [duong_ke, header, duong_ke] + cac_dong + [duong_ke]
        bang.append(f"Tổng số: {len(ds_giao_dich)} giao dịch")

        self._noi_dung = "\n".join(bang)
        return self._noi_dung


class QuanLyXuatBaoCao:
    """
    Lớp quản lý trung tâm — tương tự class Luong trong mẫu giáo viên.
    Chứa danh sách các đối tượng xuất và gọi xuat() đa hình trên tất cả.
    """

    def __init__(self, tieu_de: str):
        self._tieu_de = tieu_de
        self.__ds_xuat = []

    def them_dinh_dang(self, xuat: ABCXuatBaoCao):
        """Thêm một định dạng xuất vào danh sách."""
        self.__ds_xuat.append(xuat)

    def xuat_tat_ca(self, ds_giao_dich: list):
        """Gọi xuat() đa hình trên toàn bộ danh sách — giống tinh_luong_ht() của thầy."""
        list(map(lambda x: x.xuat(ds_giao_dich), self.__ds_xuat))

    def ds_xuat(self):
        return self.__ds_xuat

    def ket_qua_tong_hop(self) -> dict:
        """Trả về kết quả tổng hợp từ tất cả các định dạng."""
        return {x.lay_ten(): x.lay_noi_dung() for x in self.__ds_xuat}

    def __str__(self):
        return f"Xuất báo cáo: {self._tieu_de} — {len(self.__ds_xuat)} định dạng"


# ============================================================
# Demo chạy độc lập (giống if __name__ == "__main__" của thầy)
# ============================================================
if __name__ == "__main__":
    du_lieu = [
        {"date": "2025-06-01", "type": "expense", "amount": 950000, "category": "Ăn uống", "wallet": "Techcombank"},
        {"date": "2025-06-01", "type": "income", "amount": 5000000, "category": "Lương", "wallet": "Techcombank"},
        {"date": "2025-06-02", "type": "expense", "amount": 200000, "category": "Di chuyển", "wallet": "Momo"},
    ]

    # Tạo quản lý và thêm các định dạng
    ql = QuanLyXuatBaoCao("Báo cáo tháng 6/2025")
    ql.them_dinh_dang(XuatJSON())
    ql.them_dinh_dang(XuatCSV())
    ql.them_dinh_dang(XuatText())

    # Gọi đa hình
    ql.xuat_tat_ca(du_lieu)

    # In kết quả từng định dạng
    print(ql)
    for x in ql.ds_xuat():
        print(f"\n{'='*40}")
        print(f"Định dạng: {x.lay_ten()}")
        print(x.lay_noi_dung())
