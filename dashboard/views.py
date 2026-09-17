from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse

from . import models
from .forms import OrderForm, CustomerForm, SupplierForm, SupplierProductForm
from .models import Customer, Order, Supplier, SupplierProduct, ActivityLog, Task
import jdatetime


# 🗓️ تابع کمکی جهت تولید تاریخ شمسی همراه با روز هفته برای هدر
def get_formatted_jdate(target_jdate=None):
    FA_WEEKDAYS = {
        0: 'شنبه', 1: 'یکشنبه', 2: 'دوشنبه', 3: 'سه‌شنبه',
        4: 'چهارشنبه', 5: 'پنج‌شنبه', 6: 'جمعه',
    }
    if not target_jdate:
        target_jdate = jdatetime.date.today()
    
    weekday_str = FA_WEEKDAYS[target_jdate.weekday()]
    return f"{weekday_str} {target_jdate.strftime('%Y/%m/%d')}"


class CustomLoginView(LoginView):
    template_name = 'dashboard/login.html'


@never_cache
@login_required
def dashboard_home(request):
    selected_date_str = request.GET.get('date')
    today_jdate = jdatetime.date.today()

    if selected_date_str:
        current_jdate_str = selected_date_str.replace('-', '/')
    else:
        current_jdate_str = today_jdate.strftime('%Y/%m/%d')

    try:
        j_year, j_month, j_day = map(int, current_jdate_str.split('/'))
        active_jdate = jdatetime.date(j_year, j_month, j_day)
        g_date = active_jdate.togregorian()
    except (ValueError, AttributeError):
        active_jdate = today_jdate
        g_date = today_jdate.togregorian()
        current_jdate_str = today_jdate.strftime('%Y/%m/%d')

    formatted_header_jdate = get_formatted_jdate(active_jdate)

    todays_customers = Customer.objects.filter(next_followup_date=g_date)
    todays_suppliers = Supplier.objects.filter(next_followup_date=g_date)
    overdue_customers = Customer.objects.filter(
        next_followup_date__lt=g_date
    ).exclude(status__in=['BOUGHT', 'CANCELED', 'LOST'])

    g_tomorrow = g_date + timedelta(days=1)
    
    today_tasks = Task.objects.filter(due_date=g_date).order_by('is_completed', '-id')
    tomorrow_tasks = Task.objects.filter(due_date=g_tomorrow).order_by('is_completed', '-id')
    other_tasks = Task.objects.exclude(due_date__in=[g_date, g_tomorrow]).order_by('is_completed', '-id')
    
    pending_tasks_count = Task.objects.filter(is_completed=False).count()

    tomorrow_jdate = today_jdate + jdatetime.timedelta(days=1)
    tomorrow_jdate_str = tomorrow_jdate.strftime('%Y-%m-%d')

    query = request.GET.get('q')
    customer_status = request.GET.get('customer_status')
    order_status = request.GET.get('order_status')
    supplier_name = request.GET.get('supplier_name')
    priority = request.GET.get('priority')
    delivery_due = request.GET.get('delivery_due')

    if query:
        todays_customers = todays_customers.filter(
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(product_code__icontains=query)
        )
        overdue_customers = overdue_customers.filter(
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(product_code__icontains=query)
        )

    if customer_status:
        todays_customers = todays_customers.filter(status=customer_status)
        overdue_customers = overdue_customers.filter(status=customer_status)

    if priority:
        todays_customers = todays_customers.filter(priority=priority)
        overdue_customers = overdue_customers.filter(priority=priority)

    if supplier_name:
        todays_suppliers = todays_suppliers.filter(name__icontains=supplier_name)

    todays_customers = todays_customers.order_by('-priority')
    overdue_customers = overdue_customers.order_by('-priority')

    orders_qs = Order.objects.all()

    if order_status:
        orders_qs = orders_qs.filter(status=order_status)

    if delivery_due == 'NEXT_7_DAYS':
        next_week_g_date = g_date + timedelta(days=7)
        orders_qs = orders_qs.filter(expected_ready_date__range=[g_date, next_week_g_date])
    elif delivery_due == 'OVERDUE':
        orders_qs = orders_qs.filter(expected_ready_date__lt=g_date)

    in_production_count = orders_qs.filter(status='IN_PRODUCTION').count()
    ready_to_ship_count = orders_qs.filter(status='READY_TO_SHIP').count()
    in_transit_count = orders_qs.filter(status='IN_TRANSIT').count()
    ready_for_customer_count = orders_qs.filter(status='READY_FOR_CUSTOMER').count()

    context = {
        'current_jdate': formatted_header_jdate,
        'current_jdate_input': current_jdate_str.replace('/', '-'),
        'tomorrow_jdate_input': tomorrow_jdate_str,
        'todays_customers': todays_customers,
        'todays_suppliers': todays_suppliers,
        'overdue_customers': overdue_customers,
        'in_production_count': in_production_count,
        'ready_to_ship_count': ready_to_ship_count,
        'in_transit_count': in_transit_count,
        'ready_for_customer_count': ready_for_customer_count,
        'today_tasks': today_tasks,
        'tomorrow_tasks': tomorrow_tasks,
        'other_tasks': other_tasks,
        'pending_tasks_count': pending_tasks_count,
    }
    return render(request, 'dashboard/index.html', context)


# 📋 ویوهای مربوط به کارهای روزانه
@never_cache
@login_required
@require_POST
def add_task(request):
    title = request.POST.get('title')
    due_date_str = request.POST.get('due_date')
    target_day = request.POST.get('target_day')
    priority = request.POST.get('priority', 'MEDIUM')

    due_date = None
    today_jdate = jdatetime.date.today()

    if target_day == 'TODAY':
        due_date = today_jdate.togregorian()
    elif target_day == 'TOMORROW':
        due_date = (today_jdate + jdatetime.timedelta(days=1)).togregorian()
    elif due_date_str:
        try:
            clean_date = due_date_str.replace('-', '/')
            jy, jm, jd = map(int, clean_date.split('/'))
            due_date = jdatetime.date(jy, jm, jd).togregorian()
        except (ValueError, AttributeError):
            due_date = today_jdate.togregorian()
    else:
        due_date = today_jdate.togregorian()

    if title:
        Task.objects.create(
            title=title,
            due_date=due_date,
            priority=priority
        )
        messages.success(request, "کار جدید با موفقیت اضافه شد.")
    return redirect('dashboard_home')


@never_cache
@login_required
def toggle_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('dashboard_home')


@never_cache
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    messages.success(request, "کار مورد نظر حذف شد.")
    return redirect('dashboard_home')


# 👥 ویوهای مربوط به مشتریان
@never_cache
@login_required
def customer_list(request):
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search') or request.GET.get('q')

    customers = Customer.objects.all().order_by('-entry_date')

    if status_filter:
        customers = customers.filter(status=status_filter)
    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query) | Q(phone__icontains=search_query) | Q(product_code__icontains=search_query)
        )

    for customer in customers:
        if customer.next_followup_date:
            j_date = jdatetime.date.fromgregorian(date=customer.next_followup_date)
            customer.jnext_followup_date = j_date.strftime('%Y/%m/%d')
        else:
            customer.jnext_followup_date = "-"

        if customer.last_followup_date:
            j_date_last = jdatetime.date.fromgregorian(date=customer.last_followup_date)
            customer.jlast_followup_date = j_date_last.strftime('%Y/%m/%d')
        else:
            customer.jlast_followup_date = "-"

    context = {
        'customers': customers,
        'search_query': search_query,
        'status_filter': status_filter,
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/customer_list.html', context)


@never_cache
@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"مشتری «{customer.full_name}» با موفقیت اضافه شد.")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'title': 'افزودن مشتری جدید',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/customer_form.html', context)


@never_cache
@login_required
def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"اطلاعات «{customer.full_name}» با موفقیت به‌روزرسانی شد.")
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)

    context = {
        'form': form,
        'customer': customer,
        'title': f'ویرایش اطلاعات {customer.full_name}',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/customer_form.html', context)


@never_cache
@login_required
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"اطلاعات «{customer.full_name}» با موفقیت به‌روزرسانی شد.")
            return redirect(request.META.get('HTTP_REFERER', 'customer_list'))
    else:
        form = CustomerForm(instance=customer)

    logs = customer.logs.all().order_by('-date')
    orders = customer.orders.all().order_by('-order_date')

    timeline_events = []
    for log in logs:
        j_datetime = jdatetime.datetime.fromgregorian(datetime=log.date).strftime('%Y/%m/%d - %H:%M')
        text = f"[{j_datetime}] {log.action_description}"
        if log.result:
            text += f" | نتیجه: {log.result}"
        timeline_events.append(text)

    context = {
        'customer': customer,
        'form': form,
        'logs': logs,
        'orders': orders,
        'timeline_events': timeline_events,
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/customer_detail.html', context)


@never_cache
@login_required
@require_POST
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer_name = customer.full_name
    customer.delete()
    messages.success(request, f"مشتری «{customer_name}» با موفقیت حذف گردید.")
    return redirect('customer_list')


@never_cache
@login_required
@require_POST
def quick_followup(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    result_action = request.POST.get('result_action')
    next_date_str = request.POST.get('next_date')
    notes = request.POST.get('notes', '')

    action_text = "پیگیری انجام شد"
    if result_action == 'NO_ANSWER':
        action_text = 'تماس گرفته شد - پاسخ نداد'
        customer.status = 'NEED_FOLLOWUP'
    elif result_action == 'SMS_SENT':
        action_text = 'پیامک / واتساپ ارسال شد'
        customer.status = 'NEED_FOLLOWUP'
    elif result_action == 'CALL_LATER':
        action_text = 'مشتری گفت بعداً تماس بگیرید'
        customer.status = 'NEED_FOLLOWUP'
    elif result_action == 'PURCHASED':
        action_text = 'خرید انجام شد'
        customer.status = 'BOUGHT'
    elif result_action == 'CANCELLED':
        action_text = 'مشتری منصرف شد'
        customer.status = 'CANCELED'

    customer.last_action = action_text
    customer.last_followup_date = jdatetime.date.today().togregorian()

    if next_date_str:
        try:
            clean_date = next_date_str.replace('-', '/')
            jy, jm, jd = map(int, clean_date.split('/'))
            customer.next_followup_date = jdatetime.date(jy, jm, jd).togregorian()
        except (ValueError, AttributeError):
            pass
    elif customer.status in ['BOUGHT', 'CANCELED', 'LOST']:
        customer.next_followup_date = None

    customer.save()

    ActivityLog.objects.create(
        customer=customer,
        action_description=action_text,
        result=notes if notes else None
    )

    messages.success(request, f"نتیجه پیگیری برای {customer.full_name} ثبت شد.")

    return redirect(request.META.get('HTTP_REFERER', '/'))


@never_cache
@login_required
def get_customer_detail_api(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    product_code = ""
    if customer.product_code:
        product_code = customer.product_code
    elif customer.interested_product and customer.interested_product.code:
        product_code = customer.interested_product.code

    data = {
        'supplier_id': customer.supplier.id if customer.supplier else None,
        'interested_product_id': customer.interested_product.id if customer.interested_product else None,
        'product_name': product_code,
        'potential_amount': int(customer.potential_amount) if customer.potential_amount else 0,
    }
    return JsonResponse(data)


# 📦 ویوهای مربوط به سفارشات
@never_cache
@login_required
def order_list(request):
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q') or request.GET.get('search')

    orders = Order.objects.select_related('customer', 'supplier', 'product').all().order_by('-id')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(
            Q(order_code__icontains=search_query) |
            Q(product_name__icontains=search_query) |
            Q(customer__full_name__icontains=search_query) |
            Q(customer__phone__icontains=search_query)
        )

    context = {
        'orders': orders,
        'current_status': status_filter,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'search_query': search_query,
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/order_list.html', context)


@never_cache
@login_required
def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save()
            messages.success(request, f"سفارش با موفقیت ثبت شد.")
            return redirect('order_list')
    else:
        customer_id = request.GET.get('customer')
        initial_data = {}
        if customer_id:
            initial_data['customer'] = customer_id
        form = OrderForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'ثبت سفارش جدید',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/order_form.html', context)


@never_cache
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/order_detail.html', context)


@never_cache
@login_required
def order_edit(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"اطلاعات سفارش #{order.id} به‌روزرسانی شد.")
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)

    context = {
        'form': form,
        'order': order,
        'title': f'ویرایش سفارش #{order.id}',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/order_form.html', context)


@never_cache
@login_required
@require_POST
def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_id_val = order.id
    order.delete()
    messages.success(request, f"سفارش #{order_id_val} با موفقیت حذف گردید.")
    return redirect('order_list')


# 🏭 ویوهای مربوط به تامین‌کنندگان و کارگاه‌ها
@never_cache
@login_required
def supplier_list(request):
    suppliers = Supplier.objects.prefetch_related('orders__customer', 'products').all().order_by('name')

    search_query = request.GET.get('q') or request.GET.get('search')
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) |
            Q(sales_manager__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    for supplier in suppliers:
        if supplier.next_followup_date:
            supplier.jnext_followup_date = jdatetime.date.fromgregorian(date=supplier.next_followup_date).strftime('%Y/%m/%d')
        else:
            supplier.jnext_followup_date = "-"

        if supplier.last_followup_date:
            supplier.jlast_followup_date = jdatetime.date.fromgregorian(date=supplier.last_followup_date).strftime('%Y/%m/%d')
        else:
            supplier.jlast_followup_date = "-"

    context = {
        'suppliers': suppliers,
        'search_query': search_query,
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/supplier_list.html', context)


@never_cache
@login_required
def supplier_add(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f"کارگاه «{supplier.name}» با موفقیت ثبت شد.")
            return redirect('supplier_edit', supplier_id=supplier.id)
    else:
        form = SupplierForm()

    context = {
        'form': form,
        'product_form': SupplierProductForm(),
        'title': 'افزودن کارگاه جدید',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/supplier_form.html', context)


@never_cache
@login_required
def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)

    if request.method == 'POST':
        if 'add_product' in request.POST:
            product_form = SupplierProductForm(request.POST)
            if product_form.is_valid():
                product = product_form.save(commit=False)
                product.supplier = supplier
                product.save()
                messages.success(request, f"محصول «{product.name}» به کارگاه اضافه شد.")
                return redirect('supplier_edit', supplier_id=supplier.id)
            form = SupplierForm(instance=supplier)
        else:
            form = SupplierForm(request.POST, instance=supplier)
            product_form = SupplierProductForm()
            if form.is_valid():
                form.save()
                messages.success(request, f"اطلاعات کارگاه «{supplier.name}» به‌روزرسانی شد.")
                return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
        product_form = SupplierProductForm()

    context = {
        'form': form,
        'product_form': product_form,
        'supplier': supplier,
        'products': supplier.products.all(),
        'title': f'ویرایش کارگاه {supplier.name}',
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/supplier_form.html', context)


@never_cache
@login_required
def supplier_delete(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    name = supplier.name
    supplier.delete()
    messages.success(request, f"کارگاه «{name}» با موفقیت حذف گردید.")
    return redirect('supplier_list')


# --- ویوهای جدید مدیریت محصولات کارگاه ---

@never_cache
@login_required
def get_supplier_product_detail(request, product_id):
    """ارسال اطلاعات محصول کارگاه برای پر کردن فرم ویرایش (Modal)"""
    product = get_object_or_404(SupplierProduct, id=product_id)
    data = {
        'id': product.id,
        'name': product.name,
        'code': product.code or '',
        'base_price': int(product.base_price) if product.base_price else 0,
        'description': product.description or '',
    }
    return JsonResponse(data)


@never_cache
@login_required
@require_POST
def edit_supplier_product(request, product_id):
    """ویرایش کامل تمام فیلدهای محصول تولیدکننده"""
    product = get_object_or_404(SupplierProduct, id=product_id)
    supplier_id = product.supplier.id

    name = request.POST.get('name')
    code = request.POST.get('code')
    base_price_raw = request.POST.get('base_price', '0')
    description = request.POST.get('description')

    clean_price = str(base_price_raw).replace(',', '').replace('،', '').strip()
    try:
        base_price = int(clean_price)
    except ValueError:
        base_price = 0

    if name:
        product.name = name
        product.code = code
        product.base_price = base_price
        product.description = description
        product.save()
        messages.success(request, f"محصول «{product.name}» با موفقیت به‌روزرسانی شد.")
    else:
        messages.error(request, "نام محصول نمی‌تواند خالی باشد.")

    return redirect('supplier_edit', supplier_id=supplier_id)


@never_cache
@login_required
@require_POST
def delete_supplier_product(request, product_id):
    product = get_object_or_404(SupplierProduct, id=product_id)
    supplier_id = product.supplier.id
    product.delete()
    messages.success(request, "محصول با موفقیت حذف شد.")
    return redirect('supplier_edit', supplier_id=supplier_id)


@never_cache
@login_required
def get_supplier_products(request, supplier_id):
    products = SupplierProduct.objects.filter(supplier_id=supplier_id).values('id', 'name', 'code', 'base_price')
    return JsonResponse({'products': list(products)})


# 📊 داشبورد گزارشات
@never_cache
@login_required
def reports_dashboard(request):
    total_customers = Customer.objects.count()
    purchased_count = Customer.objects.filter(status='BOUGHT').count()
    cancelled_count = Customer.objects.filter(status='CANCELED').count()
    in_progress_count = Customer.objects.exclude(status__in=['BOUGHT', 'CANCELED', 'LOST']).count()

    conversion_rate = 0
    if total_customers > 0:
        conversion_rate = round((purchased_count / total_customers) * 100, 1)

    total_sales = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_received = Order.objects.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    total_pending = max(0, total_sales - total_received)

    context = {
        'total_customers': total_customers,
        'purchased_count': purchased_count,
        'cancelled_count': cancelled_count,
        'in_progress_count': in_progress_count,
        'conversion_rate': conversion_rate,
        'total_sales': total_sales,
        'total_received': total_received,
        'total_pending': total_pending,
        'in_production_orders': Order.objects.filter(status='IN_PRODUCTION').count(),
        'ready_orders': Order.objects.filter(status='READY_TO_SHIP').count(),
        'current_jdate': get_formatted_jdate(),
    }
    return render(request, 'dashboard/reports.html', context)