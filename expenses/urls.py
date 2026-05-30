from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, WalletViewSet, TransactionViewSet, BudgetViewSet, NotificationViewSet

# Sử dụng DefaultRouter để tự động định tuyến các thao tác CRUD và các Custom API Action
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('wallets', WalletViewSet, basename='wallet')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('budgets', BudgetViewSet, basename='budget')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Định tuyến tự động của ViewSet (CRUD, Reports, Transfer, Notifications)
    path('', include(router.urls)),
]
