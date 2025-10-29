from django.db.models import Q
from store.models import Category
from store import models as store_models

def cart_counter(request):
    """Return total cart items for use in all templates."""
    cart_id = request.session.get('cart_id', None)

    if cart_id or request.user.is_authenticated:
        filters = Q()
        if cart_id:
            filters |= Q(cart_id=cart_id)
        if request.user.is_authenticated:
            filters |= Q(user=request.user)

        total_cart_items = store_models.Cart.objects.filter(filters).count()
    else:
        total_cart_items = 0

    return {'total_cart_items': total_cart_items}

def categories(request):
    return {'category_': Category.objects.all()}
