from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from customer import models as customer_models
# Register your models here.
class AddressAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ['user', 'full_name']

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']

class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'seen', 'date']

admin.site.register(customer_models.Address, AddressAdmin)
admin.site.register(customer_models.Wishlist, WishlistAdmin)
admin.site.register(customer_models.Notifications, NotificationsAdmin)