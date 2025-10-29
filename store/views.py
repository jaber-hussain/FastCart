from decimal import Decimal
from itertools import product
import uuid
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from requests import request
from plugin.paginate_queryset import paginate_queryset
from plugin.service_fee import calculate_service_fee
from store import models as store_models
from customer.models import Notifications
from vendor.models import Vendor, Notifications as VendorNotifications
from customer import models as customer_models
from plugin.tax_calculation import tax_calculation
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from userauths import models as userauths_models
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify


# Create your views here.
def index(request):
    products = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()
    return render(request, 'store/index.html', {'products': products, 'categories': categories})

def product_detail(request, slug):
    product = store_models.Product.objects.get(status="Published", slug=slug)
    related_products = store_models.Product.objects.filter(status="Published", category=product.category).exclude(id=product.id)[:4]  
    product_stock_range = range(1, product.stock + 1)
    context = {
        'product': product, 
        'related_products': related_products,
        'product_stock_range': product_stock_range
    }
    return render(request, 'store/product_detail.html', context)


def add_to_cart(request):
    # Get parameters from the request
    product_id = request.GET.get("id")
    quantity = request.GET.get("quantity")
    color = request.GET.get("color")
    size = request.GET.get("size")
    if 'cart_id' not in request.session:
        request.session['cart_id'] = str(uuid.uuid4())
    cart_id = request.session['cart_id']

    # Default quantity to 1 if not provided or is invalid
    if quantity is None or not quantity.isdigit():
        quantity = 1
    else:
        quantity = int(quantity)

    # Fetch product
    try:
        product = store_models.Product.objects.get(status="Published", id=product_id)
    except store_models.Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    # Check if item already in cart
    existing_cart_item = store_models.Cart.objects.filter(cart_id=cart_id, product=product).first()

    # Check stock
    if quantity > product.stock:
        return JsonResponse({"error": "Quantity exceeds available stock"}, status=400)

    # Add or update cart
    if not existing_cart_item:
        cart_item = store_models.Cart(
            product=product,
            quantity=quantity,
            price=product.price,
            color=color,
            size=size,
            sub_total=Decimal(product.price) * Decimal(quantity),
            shipping=Decimal(product.shipping) * Decimal(quantity),
            total=Decimal(product.price) * Decimal(quantity) + Decimal(product.shipping) * Decimal(quantity),
            user=request.user if request.user.is_authenticated else None,
            cart_id=cart_id
        )
        cart_item.save()
        message = "Item added to cart"
    else:
        existing_cart_item.color = color
        existing_cart_item.size = size
        existing_cart_item.quantity = quantity
        existing_cart_item.sub_total = Decimal(product.price) * Decimal(quantity)
        existing_cart_item.shipping = Decimal(product.shipping) * Decimal(quantity)
        existing_cart_item.total = existing_cart_item.sub_total + existing_cart_item.shipping
        existing_cart_item.user = request.user if request.user.is_authenticated else None
        existing_cart_item.save()
        message = "Cart updated"

    # Count total items & sub total
    total_cart_items = store_models.Cart.objects.filter(cart_id=cart_id).count()
    cart_sub_total = store_models.Cart.objects.filter(cart_id=cart_id).aggregate(sub_total=Sum("sub_total"))['sub_total'] or 0
    item_sub_total = existing_cart_item.sub_total if existing_cart_item else cart_item.sub_total

    # Return response
    return JsonResponse({
        "message": message,
        "total_cart_items": total_cart_items,
        "cart_sub_total": "{:,.2f}".format(cart_sub_total),
        "item_sub_total": "{:,.2f}".format(item_sub_total)
    })

def cart(request):
    if 'cart_id' not in request.session:
        request.session['cart_id'] = str(uuid.uuid4())
    cart_id = request.session['cart_id']

    filters = Q(cart_id=cart_id)
    if request.user.is_authenticated:
        filters |= Q(user=request.user)

    items = store_models.Cart.objects.filter(filters)
    cart_sub_total = items.aggregate(sub_total=Sum("sub_total"))['sub_total'] or 0



    try:
        addresses = customer_models.Address.objects.filter(user=request.user)
    except:
        addresses = None

    if not items:
        messages.warning(request, "Your cart is empty. Please add some products to your cart.")
        return redirect('store:index')
    
    context = {
        'items': items,
        'cart_sub_total': cart_sub_total,
        'addresses': addresses
    }

    return render(request, 'store/cart.html', context)


def delete_cart_item(request):
    id = request.GET.get('id')
    item_id = request.GET.get('item_id')
    cart_id = request.GET.get('cart_id')

    if not id and not item_id and not cart_id:
        return JsonResponse({"error": "Item or Product ID not found"}, status=400)
    
    try:
        product = store_models.Product.objects.get(status="Published", id=id)
    except:
        return JsonResponse({"error": "Product not found"}, status=404)
    item = store_models.Cart.objects.filter(product=product, id=item_id)
    if item:
        item.delete()

    total_cart_items = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user))
    cart_sub_total = total_cart_items.aggregate(sub_total=Sum("sub_total"))['sub_total'] or 0

    return JsonResponse({
        "message": "Item removed from cart",
        "total_cart_items": total_cart_items.count(),
        "cart_sub_total": "{:,.2f}".format(cart_sub_total) if cart_sub_total else "0.00"
    })

def create_order(request):
    if request.method == "POST":
        address_id = request.POST.get("address")
        
        if not address_id:
            messages.warning(request, "Please select an address.")
            return redirect('store:cart')
        
        address = customer_models.Address.objects.get(user=request.user, id=int(address_id))

        if 'cart_id' in request.session:
            cart_id = request.session['cart_id']
        else:
            cart_id = None

        items = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id))
        cart_sub_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id)).aggregate(sub_total = Sum("sub_total"))["sub_total"] or 0
        cart_shipping_total = store_models.Cart.objects.filter(Q(cart_id=cart_id) | Q(user=request.user) if request.user.is_authenticated else Q(cart_id=cart_id)).aggregate(shipping = Sum("shipping"))["shipping"] or 0
        
        order = store_models.Order()
        order.customer = request.user if request.user.is_authenticated else None
        order.address = address
        order.sub_total = cart_sub_total
        order.shipping = cart_shipping_total
        order.tax = tax_calculation(address.country, cart_sub_total)
        order_total = cart_sub_total + order.shipping + Decimal(str(order.tax))
        order.service_fee = calculate_service_fee(order_total)
        order.total = order_total + order.service_fee
        order.initial_total = order.total
        order.save()

        for item in items:
            store_models.OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                color=item.color,
                size=item.size,
                price=item.price,
                sub_total=item.sub_total,
                shipping=item.shipping,  # snapshot from cart
                tax=tax_calculation(address.country, item.sub_total),
                total=item.total,
                initial_total=item.total,
                vendor=item.product.vendor,
                shipping_method=None,
            )

            order.vendor.add(item.product.vendor)

        return redirect('store:checkout', order_id=order.order_id)
    
def checkout(request, order_id):
    order = get_object_or_404(store_models.Order, order_id=order_id)
    items = order.order_items()  # queryset

    # Group items by vendor (key: vendor object, value: list of OrderItem)
    items_by_vendor = {}
    for it in items:
        vendor = it.vendor  # can be None
        items_by_vendor.setdefault(vendor, []).append(it)

    # Prepare a list of vendor groups (so the template can iterate)
    vendors_and_options = []
    for vendor in order.vendor.all():
        options = store_models.ShippingMethod.objects.filter(vendor=vendor, active=True)
        vendors_and_options.append({
            'vendor': vendor,
            'options': options,
            'items': items_by_vendor.get(vendor, [])
        })

    context = {
        'order': order,
        'items': items,
        'items_by_vendor': items_by_vendor,
        'vendors_and_options': vendors_and_options,
    }
    return render(request, 'store/checkout.html', context)

def update_shipping(request, order_id):
    """Handle POST from checkout: update shipping_method per vendor and recalc totals."""
    if request.method != "POST":
        return redirect('store:checkout', order_id=order_id)

    order = get_object_or_404(store_models.Order, order_id=order_id)

    # Map vendor.id -> selected ShippingMethod (or None)
    vendor_selected_sm = {}
    for vendor in order.vendor.all():
        selected_id = request.POST.get(f'shipping_for_vendor_{vendor.id}')
        if selected_id:
            try:
                sm = store_models.ShippingMethod.objects.get(id=selected_id, vendor=vendor, active=True)
            except store_models.ShippingMethod.DoesNotExist:
                sm = None
        else:
            sm = None
        vendor_selected_sm[vendor.id] = sm

    # Update each OrderItem: set shipping_method and compute shipping per item
    for item in order.order_items():
        vendor = item.vendor
        sm = vendor_selected_sm.get(vendor.id) if vendor else None

        if sm:
            # ASSUMPTION: sm.price is per unit. (If you want per-order instead, tell me & I will adapt.)
            new_shipping = (Decimal(sm.price) * Decimal(item.quantity))
            item.shipping_method = sm
            item.shipping = new_shipping
            item.shipping_service = sm.name  # keep old text field in sync while migrating
        else:
            # keep existing shipping snapshot (do not zero it)
            item.shipping_method = None
            # item.shipping remains unchanged (keeps cart snapshot)
        # Recalculate item tax (uses your helper)
        if order.address:
            item.tax = tax_calculation(order.address.country, item.sub_total)
        else:
            item.tax = Decimal('0.00')
        item.total = (item.sub_total or Decimal('0.00')) + (item.shipping or Decimal('0.00')) + Decimal(str(item.tax or 0))
        item.save(update_fields=['shipping_method', 'shipping', 'shipping_service', 'tax', 'total'])

    # Recompute order totals
    qs = order.order_items()
    sub_total = qs.aggregate(sub_total=Sum('sub_total'))['sub_total'] or Decimal('0.00')
    shipping_total = qs.aggregate(shipping=Sum('shipping'))['shipping'] or Decimal('0.00')
    tax_total = qs.aggregate(tax=Sum('tax'))['tax'] or Decimal('0.00')

    order.sub_total = sub_total
    order.shipping = shipping_total
    order.tax = tax_total

    # service fee calculation (consistent with create_order)
    order_total_before_fee = sub_total + shipping_total + Decimal(str(tax_total))
    order.service_fee = calculate_service_fee(order_total_before_fee)
    order.total = order_total_before_fee + order.service_fee
    order.initial_total = order.total
    order.save()

    messages.success(request, "Shipping options updated.")
    return redirect('store:checkout', order_id=order.order_id)

def coupon_apply(request, order_id):
    try:
        order = store_models.Order.objects.get(order_id=order_id)
        order_items = store_models.OrderItem.objects.filter(order=order)
    except store_models.Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect('store:cart')
    
    if request.method == "POST":
        coupon_code = request.POST.get("coupon_code")

        if not coupon_code:
            messages.warning(request, "Please enter a coupon code.")
            return redirect('store:checkout', order_id=order_id)
        
        try:
            coupon = store_models.Coupon.objects.get(code=coupon_code)
        except store_models.Coupon.DoesNotExist:
            messages.error(request, "Invalid coupon code.")
            return redirect('store:checkout', order_id=order_id)
        
        if coupon in order.coupons.all():
            messages.info(request, "Coupon already applied to this order.")
            return redirect('store:checkout', order_id=order_id)
        else:
            total_discount = 0

            for item in order_items:
                if coupon.vendor == item.product.vendor and coupon not in item.coupon.all():
                    item_discount = item.total * coupon.discount / 100
                    total_discount += item_discount

                    item.coupon.add(coupon)
                    item.total -= item_discount
                    item.saved += item_discount
                    item.save()

            if total_discount > 0:
                order.coupons.add(coupon)
                order.total -= total_discount
                order.sub_total -= total_discount
                order.saved += total_discount
                order.save()
                messages.success(request, f"Coupon applied successfully! You saved {total_discount:.2f}.")

        return redirect('store:checkout', order_id=order_id)
    
def process_payment(request, order, payment_method, payment_status):
    """
    Common logic: update order, adjust stock, clear cart, send notifications/emails.
    """
    # Update order
    order.payment_method = payment_method
    order.payment_status = payment_status
    order.status = "Processing"
    order.save()

    # Reduce product stock
    for item in order.order_items():
        product = item.product
        product.stock -= item.quantity
        product.save()

    if request.user.is_authenticated:
        store_models.Cart.objects.filter(user=request.user).delete()
    elif 'cart_id' in request.session:
        store_models.Cart.objects.filter(cart_id=request.session['cart_id']).delete()

    # Clear cart session
    request.session.pop('cart_id', None)

    # Notify customer
    customer_models.Notifications.objects.create(type="New Order", user=request.user)

    merge_data = {
        'order': order,
        'order_items': order.order_items(),
    }
    subject = f"Order Confirmation - {order.order_id}"
    text_body = render_to_string("email/order/customer/customer_new_order.txt", merge_data)
    html_body = render_to_string("email/order/customer/customer_new_order.html", merge_data)

    msg = EmailMultiAlternatives(subject=subject, from_email=settings.DEFAULT_FROM_EMAIL,
                                 to=["j2398797@gmail.com"], body=text_body)
    msg.attach_alternative(html_body, "text/html")
    msg.send()
    customer_models.Notifications.objects.create(type="New Order", user=request.user)

    # Notify vendors
    for item in order.order_items():
        vendor_merge_data = {'item': item}
        subject = f"New Order - {item.product.name}"
        text_body = render_to_string("email/order/vendor/vendor_new_order.txt", vendor_merge_data)
        html_body = render_to_string("email/order/vendor/vendor_new_order.html", vendor_merge_data)
        msg = EmailMultiAlternatives(subject=subject, from_email=settings.DEFAULT_FROM_EMAIL,
                                     to=["jaberi51247@gmail.com"], body=text_body)
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        VendorNotifications.objects.create(type="New Order", user=item.vendor, order=item)

    # Redirect to status page
    return redirect(f"/payment_status/{order.order_id}/?payment_status=paid")


@csrf_exempt
def cod_payment(request, order_id):
    """Cash on Delivery."""
    order = get_object_or_404(store_models.Order, order_id=order_id)
    return process_payment(request, order, store_models.PAYMENT_METHOD[0][0], "Paid")


@csrf_exempt
def credit_card_payment(request, order_id):
    """Offline Credit Card (manual charge)."""
    order = get_object_or_404(store_models.Order, order_id=order_id)
    return process_payment(request, order, store_models.PAYMENT_METHOD[1][0], "Paid")


@csrf_exempt
def jazzcash_payment(request, order_id):
    """Manual JazzCash payment."""
    order = get_object_or_404(store_models.Order, order_id=order_id)
    return process_payment(request, order, store_models.PAYMENT_METHOD[2][0], "Paid")


@csrf_exempt
def easypaisa_payment(request, order_id):
    """Manual Easypaisa payment."""
    order = get_object_or_404(store_models.Order, order_id=order_id)
    return process_payment(request, order, store_models.PAYMENT_METHOD[3][0], "Paid")


def payment_status(request, order_id):
    """Renders a generic payment status page."""
    order = get_object_or_404(store_models.Order, order_id=order_id)
    payment_status = request.GET.get("payment_status", "failed")
    return render(request, "store/payment_status.html", {
        "order": order,
        "payment_status": payment_status
    })

def about(request):
    return render(request, "pages/about.html")

def contact(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        userauths_models.ContactMessage.objects.create(
            full_name=full_name,
            email=email,
            subject=subject,
            message=message,
        )
        messages.success(request, "Message sent successfully")
        return redirect("store:contact")
    return render(request, "pages/contact.html")

def faqs(request):
    return render(request, "pages/faqs.html")

def privacy_policy(request):
    return render(request, "pages/privacy_policy.html")

def terms_conditions(request):
    return render(request, "pages/terms_conditions.html")

def shop(request):
    products_list = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()
    colors = store_models.VariantItem.objects.filter(variant__name='Color').values('title', 'content').distinct()
    sizes = store_models.VariantItem.objects.filter(variant__name='Size').values('title', 'content').distinct()
    item_display = [
        {"id": "1", "value": 1},
        {"id": "2", "value": 2},
        {"id": "3", "value": 3},
        {"id": "40", "value": 40},
        {"id": "50", "value": 50},
        {"id": "100", "value": 100},
    ]

    ratings = [
        {"id": "1", "value": "★☆☆☆☆"},
        {"id": "2", "value": "★★☆☆☆"},
        {"id": "3", "value": "★★★☆☆"},
        {"id": "4", "value": "★★★★☆"},
        {"id": "5", "value": "★★★★★"},
    ]

    prices = [
        {"id": "lowest", "value": "Highest to Lowest"},
        {"id": "highest", "value": "Lowest to Highest"},
    ]


    print(sizes)

    products = paginate_queryset(request, products_list, 10)

    context = {
        "products": products,
        "products_list": products_list,
        "categories": categories,
         'colors': colors,
        'sizes': sizes,
        'item_display': item_display,
        'ratings': ratings,
        'prices': prices,
    }
    return render(request, "store/shop.html", context)

def category(request, id):
    category = get_object_or_404(store_models.Category, id=id)
    products_list = store_models.Product.objects.filter(status="Published", category=category)

    print(f"Selected category: {category}")             # Debug
    print(f"Products found: {products_list.count()}")   # Debug

    query = request.GET.get("q")
    if query:
        products_list = products_list.filter(name__icontains=query)

    products = paginate_queryset(request, products_list, 10)

    return render(request, "store/category.html", {
        "products": products,
        "products_list": products_list,
        "category": category,
        "all_categories": store_models.Category.objects.all()  # Pass all for sidebar
    })

def search(request):
    from django.db.models import Count, Q

    query = request.GET.get("q", "").strip()
    products_list = store_models.Product.objects.filter(status="Published")
    if query:
        products_list = products_list.filter(name__icontains=query)

    products = paginate_queryset(request, products_list, 10)

    # ---  sidebar data  (LIMITED to current search results)  ---
    categories = (
        store_models.Category.objects
        .filter(product__in=products_list)          # ← only cats that have these products
        .distinct()
        .annotate(product_count=Count("product", filter=Q(product__in=products_list)))
    )

    colors = (
        store_models.VariantItem.objects
        .filter(variant__name="Color", variant__product__in=products_list)
        .values("title", "content").distinct()
    )

    sizes = (
        store_models.VariantItem.objects
        .filter(variant__name="Size", variant__product__in=products_list)
        .values("title", "content").distinct()
    )

    # static options
    item_display = [
        {"id": "1", "value": 1}, {"id": "2", "value": 2}, {"id": "3", "value": 3},
        {"id": "40", "value": 40}, {"id": "50", "value": 50}, {"id": "100", "value": 100}
    ]
    ratings = [
        {"id": "1", "value": "★☆☆☆☆"}, {"id": "2", "value": "★★☆☆☆"},
        {"id": "3", "value": "★★★☆☆"}, {"id": "4", "value": "★★★★☆"},
        {"id": "5", "value": "★★★★★"}
    ]
    prices = [
        {"id": "lowest", "value": "Highest to Lowest"},
        {"id": "highest", "value": "Lowest to Highest"}
    ]

    context = {
        "products": products,
        "products_list": products_list,
        "search_query": query,
        "categories": categories,
        "colors": colors,
        "sizes": sizes,
        "item_display": item_display,
        "ratings": ratings,
        "prices": prices,
    }
    return render(request, "store/search.html", context)

def vendors(request):
    vendors = userauths_models.Profile.objects.filter(user_type="Vendor")
    
    context = {
        "vendors": vendors
    }
    return render(request, "store/vendors.html", context)

def category_list(request):
    cats = store_models.Category.objects.all()
    return render(request, "store/category_list.html", {"categories": cats})

def category_detail(request, slug):
    category = get_object_or_404(store_models.Category, slug=slug)
    products_list = store_models.Product.objects.filter(
        status="Published", category=category
    )
    products = paginate_queryset(request, products_list, 12)
    return render(request, "store/category_detail.html", {
        "category": category,
        "products": products,
    })

def order_tracker_page(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        return redirect("store:order_tracker_detail", order_id=item_id)  # <-- use order_id
    return render(request, "store/order_tracker_page.html")


def order_tracker_detail(request, order_id):
    item = store_models.OrderItem.objects.filter(
        Q(item_id=order_id) | Q(order__order_id=order_id)
    ).first()
    
    if not item:
        messages.error(request, "Order not found!")
        return redirect("store:order_tracker_page")
    
    context = {"item": item}
    return render(request, "store/order_tracker.html", context)


def filter_products(request):
    from django.db.models import Count, Q, Avg

    # Get all filter parameters
    categories = request.GET.getlist('categories[]')
    rating = request.GET.getlist('rating[]')
    sizes = request.GET.getlist('sizes[]')
    colors = request.GET.getlist('colors[]')
    price_order = request.GET.get('prices')
    display = request.GET.get('display')
    q = request.GET.get('q', '').strip()

    # Start with ALL published products
    products = store_models.Product.objects.filter(status="Published")
    
    # Apply search query if it exists
    if q:
        products = products.filter(name__icontains=q)

    # Apply additional filters
    if categories:
        products = products.filter(category__id__in=categories)
    if rating:
        products = products.filter(reviews__rating__in=rating).distinct()
    if sizes:
        products = products.filter(variant__variant_items__content__in=sizes).distinct()
    if colors:
        products = products.filter(variant__variant_items__content__in=colors).distinct()

    # Apply price ordering
    if price_order == 'highest':
        products = products.order_by('price')
    elif price_order == 'lowest':
        products = products.order_by('-price')

    # Apply display limit
    if display:
        products = products[:int(display)]

    # Render the template
    html = render_to_string('partials/_store.html', {'products': products})
    return JsonResponse({
        'html': html,
        'product_count': products.count(),
    })

@login_required
def wishlist(request):
    wishlist_list = customer_models.Wishlist.objects.filter(user=request.user)
    wishlist = paginate_queryset(request, wishlist_list, 6)

    context = {
        "wishlist": wishlist,
        "wishlist_list": wishlist_list,
    }
    
    return render(request, "store/wishlist.html", context)

@login_required
def remove_from_wishlist(request, id):
    wishlist = customer_models.Wishlist.objects.get(user=request.user, id=id)
    wishlist.delete()
    
    messages.success(request, "item removed from wishlist")
    return redirect("store:wishlist")

