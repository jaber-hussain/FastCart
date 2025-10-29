# audit/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
import csv
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("coloured_action", "actor", "object_repr", "ip_address", "timestamp")
    list_filter = ("action", "timestamp", "content_type")
    search_fields = ("actor__email", "object_repr", "ip_address")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    date_hierarchy = "timestamp"
    actions = ["export_csv"]

    def coloured_action(self, obj):
        colours = {
            "LOGIN": "green",
            "LOGOUT": "gray",
            "CREATE": "blue",
            "UPDATE": "orange",
            "DELETE": "red",
            "CART_ADD": "cyan",
            "WISH_ADD": "purple",
            "ORDER_PLACED": "black",
        }
        return format_html(
            '<b style="color:{}">{}</b>',
            colours.get(obj.action, "black"),
            obj.get_action_display(),
        )
    coloured_action.short_description = "Action"

    def export_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=audit_log.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, f) for f in field_names])
        return response
    export_csv.short_description = "Export selected rows"