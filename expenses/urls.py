from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, WalletViewSet, TransactionViewSet, BudgetViewSet, NotificationViewSet

# Router tự động tạo endpoint CRUD cho các ViewSet
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('wallets', WalletViewSet, basename='wallet')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('budgets', BudgetViewSet, basename='budget')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
