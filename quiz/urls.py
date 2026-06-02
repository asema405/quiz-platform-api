from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, CategoryViewSet, TestViewSet, AttemptViewSet, MyResultsView, AdminTestStatisticsView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tests', TestViewSet, basename='test')
router.register(r'attempts', AttemptViewSet, basename='attempt')

urlpatterns = [
    path('', include(router.urls)),

    # Аутентификация
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Колдонуучунун жыйынтыктары
    path('my-results/', MyResultsView.as_view(), name='my_results'),

    # Админ үчүн статистика
    path('admin/tests/<int:pk>/stats/', AdminTestStatisticsView.as_view(), name='admin_test_stats'),
]