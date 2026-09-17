/**
 * مدیریت تب‌ها و مدال‌های داشبورد CRM بی‌نظیر
 */

// مدیریت تغییر تب‌ها
function openTab(evt, tabId) {
    const tabContents = document.getElementsByClassName("tab-content");
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.add("hidden");
    }

    const tabBtns = document.getElementsByClassName("tab-btn");
    for (let i = 0; i < tabBtns.length; i++) {
        tabBtns[i].classList.remove("bg-blue-600", "text-white", "shadow-md", "shadow-blue-500/20");

        // بازگرداندن استایل پیش‌فرض بر اساس نوع دکمه
        if (tabBtns[i].getAttribute('onclick').includes('tab-overdue')) {
            tabBtns[i].classList.add("text-red-600", "hover:bg-red-50");
        } else {
            tabBtns[i].classList.add("text-gray-700", "hover:bg-slate-100");
        }
    }

    // فعال‌سازی تب و دکمه انتخاب شده
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.classList.remove("hidden");
    }

    evt.currentTarget.classList.add("bg-blue-600", "text-white", "shadow-md", "shadow-blue-500/20");
    evt.currentTarget.classList.remove("text-gray-700", "hover:bg-slate-100", "text-red-600", "hover:bg-red-50");
}

// باز کردن مدال ثبت پیگیری سریع
function openModal(customerId, customerName) {
    const nameSpan = document.getElementById('modal-customer-name');
    const form = document.getElementById('followup-form');
    const modal = document.getElementById('followup-modal');

    if (nameSpan) nameSpan.innerText = customerName;
    if (form) form.action = `/customer/${customerId}/quick-followup/`;
    if (modal) modal.classList.remove('hidden');
}

// بستن مدال ثبت پیگیری
function closeModal() {
    const modal = document.getElementById('followup-modal');
    if (modal) modal.classList.add('hidden');
}

// رویدادهای پس از بارگذاری کامل صفحه
document.addEventListener('DOMContentLoaded', function () {
    // ۱. بستن مدال با کلیک روی پس‌زمینه تاریک
    const modal = document.getElementById('followup-modal');
    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // ۲. منوی کشویی موبایل
    const btn = document.getElementById('mobile-menu-btn');
    const menu = document.getElementById('mobile-menu');

    if (btn && menu) {
        btn.addEventListener('click', () => {
            menu.classList.toggle('hidden');
        });
    }
});

// ۳. ریلود کردن صفحه هنگام زدن دکمه Back مرورگر جهت به‌روزرسانی اطلاعات
window.onpageshow = function (event) {
    if (event.persisted || (performance && performance.navigation.type === 2)) {
        window.location.reload();
    }
};