# manager/views.py
import django
from pytz import timezone
import vendor


from django.utils import timezone
import decimal
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum, F, DecimalField, ExpressionWrapper
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from store import models as store_models
from django.utils.text import slugify
from userauths.decorators import manager_required
from blog.models import Blog, Category, Comment
from store.models import (
    ORDER_STATUS, PAYMENT_METHOD, PAYMENT_STATUS,
    Order, OrderItem, Product,
)
from userauths.models import User
from vendor.models import Vendor
from manager.forms import VendorForm

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
sales_expr = ExpressionWrapper(
    F('quantity') * F('price'),
    output_field=DecimalField(max_digits=10, decimal_places=2)
)

def _delete_and_redirect(model, pk, redirect_view):
    """Generic delete helper that also handles 404."""
    obj = get_object_or_404(model, pk=pk)
    obj.delete()
    return redirect(redirect_view)

# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
@manager_required
def dashboard(request):
    pending_vendor_count = Vendor.objects.filter(is_approved=False).count()

    context = {
        'products': Product.objects.count(),
        'orders': Order.objects.count(),
        'vendors': User.objects.filter(vendor__isnull=False).count(),
        'customers': User.objects.filter(customer__isnull=False).count(),
        'pending_comments': Comment.objects.filter(approved=False).count(),
        'pending_vendor_count': pending_vendor_count,   # ← NEW
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'data': [5, 10, 7, 12, 8, 15],  # replace with real analytics
    }
    return render(request, 'manager/dashboard.html', context)

# ------------------------------------------------------------------
# Simple list views
# ------------------------------------------------------------------
@manager_required
def manage_blogs(request):
    return render(request, 'manager/manage_blogs.html',
                  {'blogs': Blog.objects.select_related('category')})


@manager_required
def manage_orders(request):
    orders = (Order.objects
              .select_related('customer')
              .prefetch_related('orderitem_set__product'))
    return render(request, 'manager/manage_orders.html', {'orders': orders})

@manager_required
def manage_products(request):
    products = (Product.objects
                .select_related('category', 'vendor')
                .order_by('-id'))
    paginator = Paginator(products, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'manager/manage_products.html',
                  {'products': page, 'products_list': products})

@manager_required
def manage_users(request):
    return render(request, 'manager/manage_users.html',
                  {'users': User.objects.select_related('profile')})

# ------------------------------------------------------------------
# Comments
# ------------------------------------------------------------------
@manager_required
def manage_comments(request):
    qs = Comment.objects.select_related('blog').order_by('-date')
    pending_qs = qs.filter(approved=False)
    approved_qs = qs.filter(approved=True)

    pending_page = Paginator(pending_qs, 10).get_page(request.GET.get('pending_page'))
    approved_page = Paginator(approved_qs, 10).get_page(request.GET.get('approved_page'))

    return render(request, 'manager/manage_comments.html', {
        'pending_comments': pending_page,
        'approved_comments': approved_page,
        'comments': qs,  # total count
    })

@manager_required
@require_POST
def approve_comment(request, comment_id):
    Comment.objects.filter(pk=comment_id).update(approved=True)
    return redirect('manager:manage_comments')

@manager_required
@require_POST
def delete_comment(request, comment_id):
    return _delete_and_redirect(Comment, comment_id, 'manager:manage_comments')

# ------------------------------------------------------------------
# User / Product / Order / Blog – delete
# ------------------------------------------------------------------
@manager_required
@require_POST
def delete_user(request, user_id):
    return _delete_and_redirect(User, user_id, 'manager:manage_users')

@manager_required
@require_POST
def delete_product(request, product_id):
    return _delete_and_redirect(Product, product_id, 'manager:manage_products')

@manager_required
@require_POST
def delete_order(request, order_id):
    return _delete_and_redirect(Order, order_id, 'manager:manage_orders')

@manager_required
@require_POST
def delete_blog(request, blog_id):
    return _delete_and_redirect(Blog, blog_id, 'manager:manage_blogs')

# ------------------------------------------------------------------
# Product CRUD
# ------------------------------------------------------------------
@manager_required
def edit_product(request, product_id):
    product = get_object_or_404(store_models.Product, pk=product_id)
    categories = store_models.Category.objects.all()

    if request.method == "POST":
        # Get basic product details
        image = request.FILES.get("image")
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        description = request.POST.get("description")
        price = request.POST.get("price")
        regular_price = request.POST.get("regular_price")
        shipping = request.POST.get("shipping")
        stock = request.POST.get("stock")

        # Update product details
        product.name = name
        product.description = description
        product.price = price
        product.regular_price = regular_price
        product.shipping = shipping
        product.stock = stock

        if category_id:
            product.category = get_object_or_404(store_models.Category, pk=category_id)

        if image:  # update only if new one uploaded
            product.image = image

        product.save()

        # ===== Handle Variants =====
        variant_ids = request.POST.getlist("variant_id[]")
        variant_titles = request.POST.getlist("variant_title[]")

        if variant_ids and variant_titles:
            for i, variant_id in enumerate(variant_ids):
                variant_name = variant_titles[i]

                if variant_id:  # Update existing variant
                    variant = store_models.Variant.objects.filter(id=variant_id).first()
                    if variant:
                        variant.name = variant_name
                        variant.save()
                else:  # Create new variant
                    variant = store_models.Variant.objects.create(product=product, name=variant_name)

                # Handle variant items
                item_ids = request.POST.getlist(f"item_id_{i}[]")
                item_titles = request.POST.getlist(f"item_title_{i}[]")
                item_descriptions = request.POST.getlist(f"item_description_{i}[]")

                if item_ids and item_titles and item_descriptions:
                    for j in range(len(item_titles)):
                        item_id = item_ids[j]
                        item_title = item_titles[j]
                        item_description = item_descriptions[j]

                        if item_id:  # Update existing item
                            variant_item = store_models.VariantItem.objects.filter(id=item_id).first()
                            if variant_item:
                                variant_item.title = item_title
                                variant_item.content = item_description
                                variant_item.save()
                        else:  # Create new item
                            store_models.VariantItem.objects.create(
                                variant=variant,
                                title=item_title,
                                content=item_description
                            )

        # ===== Handle Product Gallery =====
        for file_key, image_file in request.FILES.items():
            if file_key.startswith("image_"):  # dynamically added gallery inputs
                store_models.Gallery.objects.create(product=product, image=image_file)

        messages.success(request, "Product updated successfully.")
        return redirect("manager:manage_products")

    return render(request, "manager/edit_product.html", {
        "product": product,
        "categories": categories,
        "variants": store_models.Variant.objects.filter(product=product),
        "gallery_images": store_models.Gallery.objects.filter(product=product),
    })

@manager_required
def delete_gallery_image(request, image_id):
    gallery_image = get_object_or_404(store_models.Gallery, id=image_id)
    product_id = gallery_image.product.id
    gallery_image.delete()
    messages.success(request, "Gallery image removed.")
    return redirect("manager:edit_product", product_id=product_id)

@manager_required
def delete_variant(request, variant_id):
    variant = get_object_or_404(store_models.Variant, id=variant_id)
    product_id = variant.product.id
    variant.delete()  # This will also delete items if you set CASCADE in your model
    messages.success(request, "Variant deleted successfully.")
    return redirect("manager:edit_product", product_id=product_id)


# ------------------------------------------------------------------
# Blog CRUD
# ------------------------------------------------------------------
def _handle_blog_post(request, blog=None):
    """Create or update blog from POST."""
    title = request.POST.get('title')
    content = request.POST.get('content')
    category_id = request.POST.get('category')
    image = request.FILES.get('image')

    if not title or not content:
        raise ValueError('Title and content are required.')

    category = None
    if category_id:
        category = get_object_or_404(Category, pk=category_id)

    if blog is None:
        blog = Blog()

    blog.title = title
    blog.content = content
    blog.category = category
    if image:
        blog.image = image
    blog.save()
    return blog

@manager_required
def add_blog(request):
    try:
        if request.method == 'POST':
            _handle_blog_post(request)
            messages.success(request, 'Blog added.')
            return redirect('manager:manage_blogs')
    except ValueError as e:
        messages.error(request, str(e))

    return render(request, 'manager/add_blog.html', {
        'categories': Category.objects.all(),
    })

@manager_required
def edit_blog(request, blog_id):
    blog = get_object_or_404(Blog, pk=blog_id)
    try:
        if request.method == 'POST':
            _handle_blog_post(request, blog=blog)
            messages.success(request, 'Blog updated.')
            return redirect('manager:manage_blogs')
    except ValueError as e:
        messages.error(request, str(e))

    return render(request, 'manager/edit_blog.html', {
        'blog': blog,
        'categories': Category.objects.all(),
    })

# ------------------------------------------------------------------
# Order CRUD
# ------------------------------------------------------------------
@manager_required
@transaction.atomic
def add_order(request):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=request.POST.get('product'))
        customer = get_object_or_404(User, pk=request.POST.get('customer'))
        quantity = int(request.POST.get('quantity', 1))

        order = Order.objects.create(
            customer=customer,
            payment_status='pending',
            payment_method='COD',
            order_status='processing',
            total_price=product.price * quantity,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            sub_total=product.price * quantity,
        )
        messages.success(request, 'Order created.')
        return redirect('manager:manage_orders')

    return render(request, 'manager/add_order.html', {
        'products': Product.objects.select_related('vendor'),
        'customers': User.objects.filter(customer__isnull=False),
    })

@manager_required
def edit_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.payment_status = request.POST.get('payment_status')
        order.payment_method = request.POST.get('payment_method')
        order.order_status = request.POST.get('order_status')
        order.save()
        messages.success(request, f'Order {order.order_id} updated.')
        return redirect('manager:manage_orders')

    return render(request, 'manager/edit_order.html', {
        'order': order,
        'order_items': order.orderitem_set.select_related('product'),
        'PAYMENT_STATUS': PAYMENT_STATUS,
        'PAYMENT_METHOD': PAYMENT_METHOD,
        'ORDER_STATUS': ORDER_STATUS,
    })

@manager_required
def view_order(request, order_id):
    order = get_object_or_404(Order.objects.select_related('customer'), pk=order_id)
    return render(request, 'manager/view_order.html', {'order': order})

# ------------------------------------------------------------------
# Vendor CRUD
# ------------------------------------------------------------------
@manager_required
def manage_vendors(request):
    vendors = Vendor.objects.select_related('user').order_by('-date')
    pending = vendors.filter(is_approved=False)
    approved = vendors.filter(is_approved=True)

    countries = Vendor.objects.values_list('country', flat=True).distinct().exclude(
        country__isnull=True).exclude(country='')

    return render(request, 'manager/manage_vendors.html', {
        'pending': pending,
        'approved': approved,
        'countries': countries,
    })

@manager_required
def add_vendor(request):
    form = VendorForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vendor added.')
        return redirect('manager:manage_vendors')
    return render(request, 'manager/add_vendor.html', {'form': form})

@manager_required
def edit_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    form = VendorForm(request.POST or None, request.FILES or None, instance=vendor)
    if form.is_valid():
        form.save()
        messages.success(request, 'Vendor updated.')
        return redirect('manager:manage_vendors')
    return render(request, 'manager/edit_vendor.html', {'form': form, 'vendor': vendor})

@manager_required
def view_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor.objects.select_related('user'), pk=vendor_id)
    products = (Product.objects
                .filter(vendor=vendor.user)
                .annotate(total_sales=Sum(
                    ExpressionWrapper(F('orderitem__quantity') * F('orderitem__price'),
                                      output_field=DecimalField()))
                ))
    total_vendor_sales = sum(p.total_sales or 0 for p in products)
    return render(request, 'manager/view_vendor.html', {
        'vendor': vendor,
        'products': [{'product': p, 'sales': p.total_sales or 0} for p in products],
        'total_vendor_sales': total_vendor_sales,
    })

@manager_required
@require_POST
def delete_vendor(request, vendor_id):
    return _delete_and_redirect(Vendor, vendor_id, 'manager:manage_vendors')

# ------------------------------------------------------------------
# Customers
# ------------------------------------------------------------------
@manager_required
def manage_customers(request):
    qs = User.objects.filter(
        is_staff=False, is_superuser=False, profile__user_type='Customer'
    ).order_by('-date_joined')

    if q := request.GET.get('q'):
        qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))

    customers = []
    for customer in qs.select_related('profile'):
        total_spent = (OrderItem.objects
                       .filter(order__customer=customer)
                       .aggregate(total=Sum(sales_expr))['total'] or 0)
        customers.append({
            'customer': customer,
            'total_orders': customer.order_set.count(),
            'total_spent': total_spent,
        })

    return render(request, 'manager/manage_customers.html', {
        'customers': customers,
        'query': request.GET.get('q', ''),
    })

@manager_required
def view_customer(request, customer_id):
    customer = get_object_or_404(User.objects.select_related('profile'), pk=customer_id)
    orders = (Order.objects
              .filter(customer=customer)
              .prefetch_related('orderitem_set__product'))
    total_spent = (OrderItem.objects
                   .filter(order__customer=customer)
                   .aggregate(total=Sum(sales_expr))['total'] or 0)
    return render(request, 'manager/view_customer.html', {
        'customer': customer,
        'orders': orders,
        'total_spent': total_spent,
    })

@manager_required
@require_POST
def delete_customer(request, customer_id):
    customer = get_object_or_404(
        User,
        pk=customer_id,
        is_staff=False,
        is_superuser=False,
        profile__user_type='Customer'
    )
    name = customer.username
    customer.delete()
    messages.success(request, f"Customer '{name}' has been deleted.")
    return redirect("manager:manage_customers")






@manager_required
@require_POST
def approve_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    vendor.is_approved = True
    vendor.approved_at = timezone.now()
    vendor.save()
    messages.success(request, f"Vendor {vendor.store_name} approved.")
    return redirect("manager:manage_vendors")

@manager_required
@require_POST
def reject_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    user = vendor.user
    store_name = vendor.store_name
    vendor.delete()          # keep User, delete Vendor record
    messages.warning(request, f"Vendor request for {store_name} rejected.")
    return redirect("manager:manage_vendors")

@manager_required
def view_category(request, pk):
    category = get_object_or_404(store_models.Category, pk=pk)
    products = category.product_set.all()
    return render(request, "manager/view_category.html", {"category": category, "products": products})

@manager_required
def edit_category(request, pk):
    category = get_object_or_404(store_models.Category, pk=pk)
    if request.method == "POST":
        title = request.POST.get("title")
        if title and title != category.title:
            category.title = title
            from django.utils.text import slugify
            slug = slugify(title)
            original_slug = slug
            counter = 1
            while store_models.Category.objects.filter(slug=slug).exclude(pk=pk).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            category.slug = slug
        category.save()
        return redirect("manager:manage_categories")
    return render(request, "manager/edit_category.html", {"category": category})


@manager_required
def delete_category(request, pk):
    category = get_object_or_404(store_models.Category, pk=pk)
    if request.method == "POST":
        category.delete()
        return redirect("manager:manage_categories")

@manager_required
def manage_categories(request):
    categories = store_models.Category.objects.all()
    return render(request, 'manager/manage_categories.html', {'categories': categories})

@manager_required
def add_category(request):
    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            slug = slugify(title)
            # Ensure unique slug
            original_slug = slug
            counter = 1
            while store_models.Category.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            store_models.Category.objects.create(title=title, slug=slug)
            return redirect("manager:manage_categories")
    return render(request, "manager/add_category.html")