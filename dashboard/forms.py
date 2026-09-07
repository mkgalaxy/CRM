from django import forms
from .models import Order, Customer, Supplier, SupplierProduct
import jdatetime


class CustomerForm(forms.ModelForm):
    """فرم ثبت و ویرایش اطلاعات مشتریان"""

    last_followup_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-15',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ آخرین پیگیری (شمسی)"
    )

    next_followup_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-20',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ پیگیری بعدی (شمسی)"
    )

    potential_amount = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 price-input',
            'placeholder': 'مبلغ احتمالی به تومان'
        }),
        label="مبلغ احتمالی (تومان)"
    )

    class Meta:
        model = Customer
        fields = [
            'full_name',
            'phone',
            'seller_name',
            'supplier',
            'interested_product',
            'interested_products',
            'potential_amount',
            'purchase_probability',
            'status',
            'priority',
            'followup_method',
            'last_action',
            'lost_reason',
            'notes',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثلاً: علی محمدی'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '09123456789'
            }),
            'seller_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام فروشنده مسئول'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_customer_supplier'
            }),
            'interested_product': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_customer_interested_product'
            }),
            'interested_products': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'توضیحات یا سایر محصولات مورد علاقه'
            }),
            'purchase_probability': forms.NumberInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'درصد (مثلاً 70)'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'followup_method': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'last_action': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثلاً: ارسال کاتالوگ و قیمت'
            }),
            'lost_reason': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'در صورت انصراف یا عدم خرید، دلیل آن را وارد کنید...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'توضیحات و یادداشت‌های مربوط به مشتری...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'supplier' in self.data:
            try:
                supplier_id = int(self.data.get('supplier'))
                self.fields['interested_product'].queryset = SupplierProduct.objects.filter(supplier_id=supplier_id)
            except (ValueError, TypeError):
                self.fields['interested_product'].queryset = SupplierProduct.objects.none()
        elif self.instance and self.instance.pk and getattr(self.instance, 'supplier', None):
            self.fields['interested_product'].queryset = self.instance.supplier.products.all()
        else:
            self.fields['interested_product'].queryset = SupplierProduct.objects.none()

        if self.instance and self.instance.pk:
            if self.instance.last_followup_date:
                self.fields['last_followup_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.last_followup_date
                ).strftime('%Y-%m-%d')
            if self.instance.next_followup_date:
                self.fields['next_followup_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.next_followup_date
                ).strftime('%Y-%m-%d')
            if self.instance.potential_amount:
                self.fields['potential_amount'].initial = f"{int(self.instance.potential_amount):,}"

    def clean_potential_amount(self):
        amount = self.cleaned_data.get('potential_amount')
        if amount:
            amount_str = str(amount).replace(',', '').replace('،', '').strip()
            try:
                return int(amount_str)
            except ValueError:
                raise forms.ValidationError("لطفاً مبلغ را به عدد صحیح وارد کنید.")
        return 0

    def _convert_jdate_to_gregorian(self, jdate_str):
        if not jdate_str:
            return None
        try:
            clean_date = jdate_str.replace('-', '/')
            jy, jm, jd = map(int, clean_date.split('/'))
            return jdatetime.date(jy, jm, jd).togregorian()
        except (ValueError, AttributeError):
            return None

    def save(self, commit=True):
        instance = super().save(commit=False)

        last_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('last_followup_jdate'))
        next_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('next_followup_jdate'))

        if last_date:
            instance.last_followup_date = last_date
        if next_date:
            instance.next_followup_date = next_date

        if commit:
            instance.save()
        return instance


class SupplierForm(forms.ModelForm):
    """فرم ثبت و ویرایش کارگاه‌ها"""

    last_followup_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-10',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ آخرین پیگیری (شمسی)"
    )

    next_followup_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-20',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ پیگیری بعدی کارگاه (شمسی)"
    )

    class Meta:
        model = Supplier
        fields = [
            'name',
            'phone',
            'sales_manager',
            'sales_manager_phone',
            'overall_status',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام کارگاه یا تولیدکننده'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '02112345678'
            }),
            'sales_manager': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام مسئول فروش / رابط'
            }),
            'sales_manager_phone': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '09121234567'
            }),
            'overall_status': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'توضیحات تکمیلی، آدرس یا نحوه تسویه...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.last_followup_date:
                self.fields['last_followup_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.last_followup_date
                ).strftime('%Y-%m-%d')
            if self.instance.next_followup_date:
                self.fields['next_followup_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.next_followup_date
                ).strftime('%Y-%m-%d')

    def _convert_jdate_to_gregorian(self, jdate_str):
        if not jdate_str:
            return None
        try:
            clean_date = jdate_str.replace('-', '/')
            jy, jm, jd = map(int, clean_date.split('/'))
            return jdatetime.date(jy, jm, jd).togregorian()
        except (ValueError, AttributeError):
            return None

    def save(self, commit=True):
        instance = super().save(commit=False)

        last_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('last_followup_jdate'))
        next_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('next_followup_jdate'))

        if last_date:
            instance.last_followup_date = last_date
        if next_date:
            instance.next_followup_date = next_date

        if commit:
            instance.save()
        return instance


class SupplierProductForm(forms.ModelForm):
    """فرم ثبت محصولات مربوط به هر تولیدکننده"""

    base_price = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 price-input',
            'placeholder': 'قیمت پایه (تومان)'
        }),
        label="قیمت پایه (تومان)"
    )

    class Meta:
        model = SupplierProduct
        fields = ['name', 'code', 'base_price', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'نام محصول (مثلا: کاناپه ۳ نفره لمسه)'
            }),
            'code': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'کد یا مدل محصول'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'توضیحات پارچه، ابعاد یا ویژگی‌های محصول...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.base_price:
            self.fields['base_price'].initial = f"{int(self.instance.base_price):,}"

    def clean_base_price(self):
        price = self.cleaned_data.get('base_price')
        if price:
            price_str = str(price).replace(',', '').replace('،', '').strip()
            try:
                return int(price_str)
            except ValueError:
                raise forms.ValidationError("لطفاً قیمت را به عدد صحیح وارد کنید.")
        return 0


class OrderForm(forms.ModelForm):
    """فرم ثبت و ویرایش سفارشات"""

    order_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-01',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ ثبت سفارش (شمسی)"
    )

    supplier_order_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-10',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ ثبت به کارگاه (شمسی)"
    )

    expected_ready_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-20',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ احتمالی آماده شدن (شمسی)"
    )

    delivery_to_customer_jdate = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '1405-05-25',
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
        }),
        label="تاریخ تحویل به مشتری (شمسی)"
    )

    total_amount = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 price-input',
            'placeholder': 'مبلغ کل به تومان'
        }),
        label="مبلغ کل (تومان)"
    )

    paid_amount = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 price-input',
            'placeholder': 'مبلغ بیعانه / پرداختی به تومان'
        }),
        label="مبلغ پرداختی (تومان)"
    )

    class Meta:
        model = Order
        fields = [
            'customer',
            'supplier',
            'product',
            'product_name',
            'order_code',
            'status',
            'total_amount',
            'paid_amount',
            'description',
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_customer'
            }),
            'supplier': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_supplier'
            }),
            'product': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_product'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'id': 'id_product_name',
                'placeholder': 'عنوان/جزئیات دقیق کالا'
            }),
            'order_code': forms.TextInput(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'مثلاً: ORD-1001'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-xl p-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'توضیحات و یادداشت‌های سفارش...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['customer'].label_from_instance = lambda obj: f"{obj.full_name} ({obj.phone})"

        if 'supplier' in self.data:
            try:
                supplier_id = int(self.data.get('supplier'))
                self.fields['product'].queryset = SupplierProduct.objects.filter(supplier_id=supplier_id)
            except (ValueError, TypeError):
                self.fields['product'].queryset = SupplierProduct.objects.none()
        elif self.instance and self.instance.pk and getattr(self.instance, 'supplier', None):
            self.fields['product'].queryset = self.instance.supplier.products.all()
        else:
            self.fields['product'].queryset = SupplierProduct.objects.none()

        if self.instance and self.instance.pk:
            if self.instance.total_amount:
                self.fields['total_amount'].initial = f"{int(self.instance.total_amount):,}"
            if self.instance.paid_amount:
                self.fields['paid_amount'].initial = f"{int(self.instance.paid_amount):,}"

            if self.instance.order_date:
                self.fields['order_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.order_date
                ).strftime('%Y-%m-%d')
            if self.instance.supplier_order_date:
                self.fields['supplier_order_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.supplier_order_date
                ).strftime('%Y-%m-%d')
            if self.instance.expected_ready_date:
                self.fields['expected_ready_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.expected_ready_date
                ).strftime('%Y-%m-%d')
            if self.instance.delivery_to_customer_date:
                self.fields['delivery_to_customer_jdate'].initial = jdatetime.date.fromgregorian(
                    date=self.instance.delivery_to_customer_date
                ).strftime('%Y-%m-%d')

    def clean_total_amount(self):
        val = self.cleaned_data.get('total_amount')
        if val:
            clean_val = str(val).replace(',', '').replace('،', '').strip()
            try:
                return int(clean_val)
            except ValueError:
                raise forms.ValidationError("مبلغ کل را معتبر وارد کنید.")
        return 0

    def clean_paid_amount(self):
        val = self.cleaned_data.get('paid_amount')
        if val:
            clean_val = str(val).replace(',', '').replace('،', '').strip()
            try:
                return int(clean_val)
            except ValueError:
                raise forms.ValidationError("مبلغ پرداختی را معتبر وارد کنید.")
        return 0

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_amount')
        paid = cleaned_data.get('paid_amount')

        if total is not None and paid is not None:
            if paid > total:
                self.add_error('paid_amount', 'مبلغ پرداختی نمی‌تواند بیشتر از مبلغ کل سفارش باشد.')

        return cleaned_data

    def _convert_jdate_to_gregorian(self, jdate_str):
        if not jdate_str:
            return None
        try:
            clean_date = jdate_str.replace('-', '/')
            jy, jm, jd = map(int, clean_date.split('/'))
            return jdatetime.date(jy, jm, jd).togregorian()
        except (ValueError, AttributeError):
            return None

    def save(self, commit=True):
        instance = super().save(commit=False)

        ord_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('order_jdate'))
        supp_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('supplier_order_jdate'))
        exp_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('expected_ready_jdate'))
        deliv_date = self._convert_jdate_to_gregorian(self.cleaned_data.get('delivery_to_customer_jdate'))

        if ord_date:
            instance.order_date = ord_date
        if supp_date:
            instance.supplier_order_date = supp_date
        if exp_date:
            instance.expected_ready_date = exp_date
        if deliv_date:
            instance.delivery_to_customer_date = deliv_date

        if commit:
            instance.save()
        return instance