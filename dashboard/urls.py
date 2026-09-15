from django.urls import path
from . import views

urlpatterns = [
    # 🏠 صفحه اصلی داشبورد و ورود
    path('', views.dashboard_home, name='dashboard_home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),

    # 📋 مسیرهای کارهای روزانه (Todo List)
    path('tasks/add/', views.add_task, name='add_task'),
    path('tasks/<int:task_id>/toggle/', views.toggle_task, name='toggle_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    # 👥 مسیرهای مشتریان (Customers)
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:customer_id>/quick-followup/', views.quick_followup, name='quick_followup'),
    path('customers/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),

    path('customer/<int:customer_id>/quick-followup/', views.quick_followup),
    path('customer/<int:customer_id>/delete/', views.customer_delete),

    # 📦 مسیرهای سفارش‌ها (Orders)
    path('orders/', views.order_list, name='order_list'),
    path('orders/add/', views.create_order, name='order_add'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:order_id>/delete/', views.order_delete, name='order_delete'),

    # 🏭 مسیرهای کارگاه‌ها / تولیدکنندگان (Suppliers & Products)
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),
    
    # 🛋️ مسیرهای عملیاتی روی محصولات کارگاه
    path('suppliers/products/<int:product_id>/detail/', views.get_supplier_product_detail, name='get_supplier_product_detail'),
    path('suppliers/products/<int:product_id>/edit/', views.edit_supplier_product, name='edit_supplier_product'),
    path('suppliers/products/<int:product_id>/delete/', views.delete_supplier_product, name='delete_supplier_product'),

    # APIها
    path('api/suppliers/<int:supplier_id>/products/', views.get_supplier_products, name='get_supplier_products'),
    path('api/customers/<int:customer_id>/detail/', views.get_customer_detail_api, name='get_customer_detail_api'),
    path('api/get-products-by-suppliers/', views.get_products_by_suppliers, name='get_products_by_suppliers'),

    # 📊 گزارشات (Reports)
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
]