from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
User = get_user_model()
ACTIONS = [
("CREATE", "CREATE"),
("UPDATE", "UPDATE"),
("DELETE", "DELETE"),
("LOGIN", "LOGIN"),
("LOGOUT", "LOGOUT"),
("CART_ADD", "CART_ADD"),
("CART_REM", "CART_REM"),
("WISH_ADD", "WISH_ADD"),
("WISH_REM", "WISH_REM"),
("ORDER_PLACED", "ORDER_PLACED"),
("REVIEW_ADD", "REVIEW_ADD"),
("VENDOR_APPLY", "VENDOR_APPLY"),
("VENDOR_APPROVE", "VENDOR_APPROVE"),
("VENDOR_REJECT", "VENDOR_REJECT"),
]
class AuditLog(models.Model):
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS, db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_repr = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["actor", "-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
        ]

def __str__(self):
    return f"{self.actor} {self.action} {self.object_repr} @ {self.timestamp:%Y-%m-%d %H:%M:%S}"