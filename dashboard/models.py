from typing import Any
from django.db import models
from django.utils import timezone


# --- ۱. مدل تولیدکنندگان ---
class Supplier(models.Model):
    COLLABORATION_STATUS_CHOICES = [
        ('ACTIVE', '🟢 فعال و عالی'),
        ('MEDIUM', '🟡 معمولی'),
        ('PROBLEM', '🟠 دارای تاخیر / مشکل'),
        ('SUSPENDED', '⚪ معلق / موقت'),
        ('INACTIVE', '🔴 غیرفعال / قطع همکاری'),
    ]

    name = models.CharField(max_length=200, verbose_name="نام تولیدی / کارگاه")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس کارگاه")
    sales_manager = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام مسئول فروش")
    sales_manager_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="شماره همراه مسئول فروش")

    last_followup_date = models.DateField(blank=True, null=True, verbose_name="تاریخ آخرین پیگیری")
    next_followup_date = models.DateField(blank=True, null=True, verbose_name="تاریخ پیگیری بعدی")

    overall_status = models.CharField(
        max_length=20,
        choices=COLLABORATION_STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="وضعیت کلی همکاری"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات و یادداشت‌ها")

    @property
    def active_orders_count(self) -> int:
        """تعداد سفارش‌های فعال (تحویل مشتری نشده)"""
        return self.orders.exclude(status='DELIVERED').count()

    def __str__(self):
        return self.name


# --- ۱.۱ مدل محصولات تولیدکننده ---
class SupplierProduct(models.Model):
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name="تولیدکننده"
    )
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name="کد/مدل محصول")
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="قیمت پایه (تومان)"
    )
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات محصول")

    def __str__(self):
        return f"{self.name} - کد: {self.code or '---'} ({self.supplier.name})"


# --- ۲. مدل مشتریان ---
class Customer(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'مشتری جدید / تازه وارد'),
        ('CHECKING', 'در حال بررسی محصول'),
        ('LIKED', 'محصول را پسندیده'),
        ('INVOICE', 'فاکتور صادر شده'),
        ('DECIDING', 'منتظر تصمیم مشتری'),
        ('NEED_FOLLOWUP', 'نیاز به پیگیری'),
        ('FOLLOWED_UP', 'پیگیری انجام شد'),
        ('BOUGHT', 'مشتری خرید کرد'),
        ('PAUSED', 'مشتری فعلاً خرید نکرد'),
        ('CANCELED', 'مشتری منصرف شد'),
        ('LOST', 'مشتری از دست رفته'),
        ('WAITING_DELIVERY', 'خرید انجام شده و منتظر تحویل'),
        ('DELIVERED', 'سفارش تحویل داده شد'),
        ('POST_PURCHASE_FOLLOWUP', 'مشتری بعد از خرید نیاز به پیگیری دارد'),
    ]

    PRIORITY_CHOICES = [
        ('CRITICAL', '🔴 خیلی مهم (آماده خرید/فاکتور/احتمال بالا)'),
        ('HIGH', '🟠 مهم (پسندیده/بدون تصمیم نهایی)'),
        ('MEDIUM', '🟡 متوسط (علاقه‌مند/در حال بررسی)'),
        ('LOW', '⚪ کم اهمیت (بدون قصد خرید مشخص)'),
    ]

    FOLLOWUP_METHOD_CHOICES = [
        ('CALL', 'تماس تلفنی'),
        ('WHATSAPP', 'واتساپ'),
        ('SMS', 'پیامک'),
        ('TELEGRAM', 'تلگرام'),
        ('IN_PERSON', 'حضوری'),
        ('OTHER', 'سایر روش‌ها'),
    ]

    full_name = models.CharField(max_length=200, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    entry_date = models.DateField(auto_now_add=True, verbose_name="تاریخ ورود")
    seller_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام فروشنده")

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name="تولیدکننده مدنظر"
    )
    interested_product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interested_customers',
        verbose_name="محصول مورد علاقه (انتخابی)"
    )

    # فیلد جدید: کد / مدل محصول (جایگزین فیلد قدیمی توضیحات)
    product_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="کد / مدل محصول")
    
    potential_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ احتمالی خرید (تومان)")
    purchase_probability = models.IntegerField(default=50, verbose_name="احتمال خرید (درصد)")

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NEW', verbose_name="وضعیت مشتری")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM', verbose_name="اولویت")

    last_action = models.CharField(max_length=255, blank=True, null=True, verbose_name="آخرین اقدام انجام شده")
    last_followup_date = models.DateField(blank=True, null=True, verbose_name="تاریخ آخرین پیگیری")
    next_followup_date = models.DateField(blank=True, null=True, verbose_name="تاریخ پیگیری بعدی")
    
    followup_time = models.CharField(max_length=10, blank=True, null=True, verbose_name="ساعت یادآوری بعدی (HH:MM)")

    followup_method = models.CharField(
        max_length=50,
        choices=FOLLOWUP_METHOD_CHOICES,
        default='CALL',
        verbose_name="روش پیگیری"
    )

    lost_reason = models.TextField(blank=True, null=True, verbose_name="دلیل نخریدن / انصراف")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def save(self, *args, **kwargs):
        # پر کردن خودکار کد/مدل محصول در صورت انتخاب محصول تولیدکننده
        if self.interested_product and self.interested_product.code:
            self.product_code = self.interested_product.code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.phone}) - {self.get_priority_display()}"


# --- ۳. مدل سفارشات ---
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('REGISTERED', 'سفارش ثبت شد'),
        ('SENT_TO_SUPPLIER', 'سفارش برای تولیدکننده ارسال شد'),
        ('SUPPLIER_CONFIRMED', 'تأیید تولیدکننده دریافت شد'),
        ('IN_PRODUCTION', 'در حال تولید'),
        ('READY_TO_SHIP', 'آماده ارسال'),
        ('GIVEN_TO_CARRIER', 'تحویل باربری شد'),
        ('IN_TRANSIT', 'در مسیر'),
        ('ARRIVED_STORE', 'به فروشگاه رسید'),
        ('READY_FOR_CUSTOMER', 'آماده تحویل به مشتری'),
        ('DELIVERED', 'تحویل مشتری شد'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders', verbose_name="مشتری")
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="تولیدکننده"
    )
    product = models.ForeignKey(
        SupplierProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="محصول انتخابی"
    )
    
    # تغییر عنوان فیلد به کد / مدل محصول
    product_name = models.CharField(max_length=200, verbose_name="کد / مدل محصول")
    order_code = models.CharField(max_length=50, unique=True, verbose_name="کد/شماره سفارش")

    order_date = models.DateField(blank=True, null=True, verbose_name="تاریخ ثبت سفارش")
    supplier_order_date = models.DateField(blank=True, null=True, verbose_name="تاریخ ثبت برای تولیدکننده")
    expected_ready_date = models.DateField(blank=True, null=True, verbose_name="تاریخ احتمالی آماده شدن")
    freight_delivery_date = models.DateField(blank=True, null=True, verbose_name="تاریخ تحویل به باربری")
    shipping_date = models.DateField(blank=True, null=True, verbose_name="تاریخ ارسال")
    store_arrival_date = models.DateField(blank=True, null=True, verbose_name="تاریخ رسیدن به فروشگاه")
    delivery_to_customer_date = models.DateField(blank=True, null=True, verbose_name="تاریخ تحویل به مشتری")

    status = models.CharField(
        max_length=30,
        choices=ORDER_STATUS_CHOICES,
        default='REGISTERED',
        verbose_name="وضعیت سفارش"
    )

    total_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ سفارش (تومان)")
    paid_amount = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="مبلغ پرداخت شده (تومان)")

    description = models.TextField(blank=True, null=True, verbose_name="توضیحات و وضعیت سفارش")

    @property
    def remaining_amount(self):
        return max(0, self.total_amount - self.paid_amount)

    @property
    def remaining_balance(self):
        rem = self.remaining_amount
        return f"{int(rem):,}" if rem > 0 else "0"

    @property
    def formatted_total_amount(self):
        return f"{int(self.total_amount):,}" if self.total_amount else "0"

    @property
    def formatted_paid_amount(self):
        return f"{int(self.paid_amount):,}" if self.paid_amount else "0"

    def __str__(self):
        return f"سفارش {self.order_code} - {self.customer.full_name}"


# --- ۴. مدل تایم‌لاین ---
class ActivityLog(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='logs', verbose_name="مشتری")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ و زمان")
    action_description = models.TextField(verbose_name="شرح اقدام / تغییر وضعیت")
    result = models.CharField(max_length=100, blank=True, null=True, verbose_name="نتیجه تماس/اقدام")

    def __str__(self):
        return f"{self.customer.full_name} - {self.date.strftime('%Y-%m-%d %H:%M')}"


# --- ۵. مدل وظایف (Task) ---
class Task(models.Model):
    TASK_PRIORITY_CHOICES = [
        ('HIGH', '🔴 بالا'),
        ('MEDIUM', '🟡 متوسط'),
        ('LOW', '🟢 پایین'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان کار / یادآوری")
    due_date = models.DateField(blank=True, null=True, verbose_name="تاریخ سررسید")
    due_time = models.CharField(max_length=10, blank=True, null=True, verbose_name="ساعت (HH:MM)")
    priority = models.CharField(
        max_length=10,
        choices=TASK_PRIORITY_CHOICES,
        default='MEDIUM',
        verbose_name="اولویت"
    )
    is_completed = models.BooleanField(default=False, verbose_name="انجام شده؟")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def __str__(self):
        return f"{self.title} - {'✅' if self.is_completed else '⏳'}"