from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from . import api_views

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'suppliers', api_views.SupplierViewSet, basename='api-supplier')
router.register(r'restaurants', api_views.RestaurantViewSet, basename='api-restaurant')
router.register(r'food', api_views.FoodViewSet, basename='api-food')
router.register(r'agents', api_views.AgentsViewSet, basename='api-agents')
router.register(r'customers', api_views.CustomerViewSet, basename='api-customer')
router.register(r'orders', api_views.OrderDetailsViewSet, basename='api-order')
router.register(r'feedback', api_views.FeedbackViewSet, basename='api-feedback')

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Restaurants CRUD
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/edit/', views.restaurant_update, name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurant_delete'),

    # Food CRUD
    path('food/', views.food_list, name='food_list'),
    path('food/create/', views.food_create, name='food_create'),
    path('food/<int:pk>/edit/', views.food_update, name='food_update'),
    path('food/<int:pk>/delete/', views.food_delete, name='food_delete'),

    # Suppliers CRUD
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Agents CRUD
    path('agents/', views.agent_list, name='agent_list'),
    path('agents/create/', views.agent_create, name='agent_create'),
    path('agents/<int:pk>/edit/', views.agent_update, name='agent_update'),
    path('agents/<int:pk>/delete/', views.agent_delete, name='agent_delete'),

    # Customers CRUD
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Orders CRUD
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_update, name='order_update'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Feedback CRUD
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('feedback/create/', views.feedback_create, name='feedback_create'),
    path('feedback/<int:pk>/edit/', views.feedback_update, name='feedback_update'),
    path('feedback/<int:pk>/delete/', views.feedback_delete, name='feedback_delete'),

    # DBMS Queries Live Demo
    path('queries-demo/', views.dbms_queries_demo, name='dbms_queries_demo'),

    # Stored Procedure Demo
    path('customer-orders-procedure/', views.customer_orders_procedure, name='customer_orders_procedure'),
    path('cursor-revenue-procedure/', views.cursor_revenue_procedure, name='cursor_revenue_procedure'),
    path('trigger-audit/', views.trigger_audit_demo, name='trigger_audit_demo'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/dashboard-stats/', api_views.dashboard_stats_api, name='api_dashboard_stats'),
    path('api/food-by-restaurant/<int:restaurant_id>/', api_views.food_by_restaurant_api, name='api_food_by_restaurant'),
]
