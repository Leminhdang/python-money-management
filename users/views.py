from rest_framework import status, viewsets, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import User
from .serializers import UserSerializer, RegisterSerializer, LoginSerializer


class RegisterAPIView(APIView):
    """API đăng ký tài khoản mới. Cho phép truy cập tự do (AllowAny)."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Đăng ký tài khoản thành công!",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """API đăng nhập, trả về JWT Token + thông tin user."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """API xem và cập nhật thông tin cá nhân của user đang đăng nhập."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Cập nhật thông tin cá nhân thành công!",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAdminViewSet(viewsets.ModelViewSet):
    """ViewSet cho Admin quản lý toàn bộ user trong hệ thống."""

    queryset = User.objects.all().order_by('-createdAt')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
