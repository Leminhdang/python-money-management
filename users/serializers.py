from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer hiển thị và cập nhật thông tin cá nhân User."""

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name', 'birthday', 'phoneNumber', 'address', 'createdAt')
        read_only_fields = ('id', 'username', 'createdAt')


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer xử lý đăng ký tài khoản mới.
    Mật khẩu được băm an toàn qua create_user() của AbstractUser.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6, label="Mật khẩu")
    passwordConfirm = serializers.CharField(write_only=True, required=True, label="Xác nhận mật khẩu")

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'passwordConfirm', 'name', 'birthday', 'phoneNumber', 'address')

    def validate(self, attrs):
        # Check mật khẩu có trùng nhau ko
        if attrs['password'] != attrs['passwordConfirm']:
            raise serializers.ValidationError({"passwordConfirm": "Mật khẩu xác nhận ko trùng khớp."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email này đã được sử dụng."})

        return attrs

    def create(self, validated_data):
        # Bỏ passwordConfirm ra trước khi tạo user
        validated_data.pop('passwordConfirm')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            birthday=validated_data.get('birthday', None),
            phoneNumber=validated_data.get('phoneNumber', ''),
            address=validated_data.get('address', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer xác thực user và sinh JWT Token.
    Hỗ trợ đăng nhập bằng cả username hoặc email.
    """
    usernameOrEmail = serializers.CharField(write_only=True, required=True, label="Tài khoản hoặc Email")
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Mật khẩu")

    # Các trường trả về khi login thành công
    user = UserSerializer(read_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    def validate(self, attrs):
        username_or_email = attrs.get('usernameOrEmail')
        password = attrs.get('password')

        # Nếu nhập email thì tìm username tương ứng
        username = username_or_email
        if '@' in username_or_email:
            try:
                user_found = User.objects.get(email=username_or_email)
                username = user_found.username
            except User.DoesNotExist:
                pass

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Tài khoản hoặc mật khẩu không chính xác.")

        if not user.is_active:
            raise serializers.ValidationError("Tài khoản này đã bị khóa.")

        # Sinh JWT token
        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }
