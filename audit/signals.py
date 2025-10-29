# audit/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.signals import user_logged_in, user_logged_out

from audit.models import AuditLog, ACTIONS
from audit.middleware import get_current_request
from audit.utils import get_client_ip

from store.models import Cart, Order, Review, Product
from customer.models import Wishlist
from vendor.models import Vendor

User = get_user_model()

# ------------------------------------------------------------------
# helper
# ------------------------------------------------------------------
def _log(actor, action, instance=None, metadata=None):
    request = get_current_request()
    ip  = get_client_ip(request) if request else None
    ua  = request.META.get("HTTP_USER_AGENT") if request else None
    AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=ContentType.objects.get_for_model(instance) if instance else None,
        object_id=str(instance.pk) if instance else None,
        object_repr=str(instance)[:255],
        metadata=metadata or {},
        ip_address=ip,
        user_agent=ua,
    )

# ------------------------------------------------------------------
# auth
# ------------------------------------------------------------------
@receiver(user_logged_in)
def on_login(sender, request, user, **kw):
    _log(user, "LOGIN")

@receiver(user_logged_out)
def on_logout(sender, request, user, **kw):
    _log(user, "LOGOUT")

# ------------------------------------------------------------------
# user created
# ------------------------------------------------------------------
@receiver(post_save, sender=User)
def on_user_create(sender, instance, created, **kw):
    if created:
        _log(instance, "CREATE", instance, {"via": "sign-up"})

# ------------------------------------------------------------------
# cart
# ------------------------------------------------------------------
@receiver(post_save, sender=Cart)
def on_cart_add(sender, instance, created, **kw):
    if created:
        _log(instance.user, "CART_ADD", instance.product,
             {"qty": instance.quantity})

@receiver(post_delete, sender=Cart)
def on_cart_rem(sender, instance, **kw):
    _log(instance.user, "CART_REM", instance.product,
         {"qty": instance.quantity})

# ------------------------------------------------------------------
# wishlist
# ------------------------------------------------------------------
@receiver(post_save, sender=Wishlist)
def on_wish_add(sender, instance, created, **kw):
    if created:
        _log(instance.user, "WISH_ADD", instance.product)

@receiver(post_delete, sender=Wishlist)
def on_wish_rem(sender, instance, **kw):
    _log(instance.user, "WISH_REM", instance.product)

# ------------------------------------------------------------------
# order placed
# ------------------------------------------------------------------
@receiver(post_save, sender=Order)
def on_order(sender, instance, created, **kw):
    if created:
        _log(instance.customer, "ORDER_PLACED", instance,
             {"total": str(instance.total)})

# ------------------------------------------------------------------
# review
# ------------------------------------------------------------------
@receiver(post_save, sender=Review)
def on_review(sender, instance, created, **kw):
    if created:
        _log(instance.user, "REVIEW_ADD", instance.product,
             {"rating": instance.rating})

# ------------------------------------------------------------------
# vendor
# ------------------------------------------------------------------
@receiver(post_save, sender=Vendor)
def on_vendor(sender, instance, created, **kw):
    if created:
        _log(instance.user, "VENDOR_APPLY", instance,
             {"store": instance.store_name})
    else:
        # detect approval / rejection
        old = Vendor.objects.filter(pk=instance.pk).first()
        if old and not old.is_approved and instance.is_approved:
            _log(None, "VENDOR_APPROVE", instance,
                 {"store": instance.store_name, "by": "manager"})
        elif old and old.is_approved and not instance.is_approved:
            _log(None, "VENDOR_REJECT", instance,
                 {"store": instance.store_name, "by": "manager"})