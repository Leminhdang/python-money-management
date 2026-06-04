from rest_framework_simplejwt.authentication import JWTAuthentication


class SwaggerJWTAuthentication(JWTAuthentication):
    """
    Chấp nhận cả 2 format:
      - "Bearer eyJhbGci..."
      - "eyJhbGci..."          (chỉ token, Swagger tiện hơn)
    """

    def get_header(self, request):
        header = super().get_header(request)
        if header is not None:
            # Nếu user chỉ nhập token thuần (không có prefix Bearer)
            # thì tự thêm prefix vào để JWTAuthentication xử lý được
            header_str = header.decode('utf-8') if isinstance(header, bytes) else header
            if not header_str.startswith('Bearer '):
                header = f'Bearer {header_str}'.encode('utf-8')
        return header
