# context_processors.py
from .models import Wishlist
from django.db.models import Q

def wishlist_counter(request):
    """
    Return total wishlist items for use in all templates.
    Works for both logged-in users and guests (session-based wishlist).
    """
    total_wishlist_items = 0

    # If user is logged in
    if request.user.is_authenticated:
        total_wishlist_items = Wishlist.objects.filter(user=request.user).count()
    else:
        # For guests, use session-based wishlist
        wishlist_id = request.session.get('wishlist_id', None)
        if wishlist_id:
            total_wishlist_items = Wishlist.objects.filter(wishlist_id=wishlist_id).count()

    return {'total_wishlist_items': total_wishlist_items}
