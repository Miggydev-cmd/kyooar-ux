from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, InventoryViewSet, InventoryLogViewSet, PingView

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('inventory', InventoryViewSet)
router.register('logs', InventoryLogViewSet, basename='logs')

urlpatterns = [
    path('', include(router.urls)),
    path('ping/', PingView.as_view(), name='ping'),
    path('register/', AuthViewSet.as_view({'post': 'register', 'get': 'register'}), name='register'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='login'),
    path('auth/login/qr/', AuthViewSet.as_view({'post': 'login_qr'}), name='login-qr'),
]
