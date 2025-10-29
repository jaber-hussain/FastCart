from django.contrib import admin
from vendor import models as vendor_models

# Register your models here.
class VendorAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'user', 'country', 'vendor_id', 'date']
    search_fields = ['store_name', 'vendor_id', 'user__username']
    list_filter = ['date', 'country']
    prepopulated_fields = {'slug': ('store_name',)}

class PayoutAdmin(admin.ModelAdmin):
    list_display = ['payout_id','vendor', 'item', 'amount', 'date']
    search_fields = ['vendor__store_name', 'payout_id', 'item__order__order_id']
    list_filter = ['date','vendor']

class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'bank_name', 'account_number', 'account_type']
    search_fields = ['vendor__store_name', 'bank_name', 'account_number', 'account_name']
    list_filter = ['account_type']

class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'order', 'seen']
    list_filter = ['order']

admin.site.register(vendor_models.Vendor, VendorAdmin)
admin.site.register(vendor_models.Payout, PayoutAdmin)
admin.site.register(vendor_models.BankAccount, BankAccountAdmin)
admin.site.register(vendor_models.Notifications, NotificationsAdmin)