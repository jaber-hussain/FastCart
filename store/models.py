from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

from userauths import models as user_models
import shortuuid
# Create your models here.

STATUS = (
    ("Published", "Published"),
    ("Draft", "Draft"),
    ("Disabled", "Disabled")
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", "Failed")
)

PAYMENT_METHOD = (
    ("Cash on Delivery", "Cash on Delivery"),
    ("Credit Card", "Credit Card"),
    ("JazzCash", "JazzCash"),
    ("Easypaisa", "Easypaisa"),
)

ORDER_STATUS = (
    ("Pending", "Pending"),
    ("Processing", "Processing"),
    ("Shipped", "Shipped"),
    ("Fulfilled", "Fulfilled"),
    ("Cancelled", "Cancelled")
)

RATING = (
    (1, " ★☆☆☆☆"),
    (2, " ★★☆☆☆"),
    (3, " ★★★☆☆"),
    (4, " ★★★★☆"),
    (5, " ★★★★★")
)

class Category(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='image', blank=True, null=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['title']

class Product(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='image', blank=True, null=True, default='product.png')
    description = CKEditor5Field('Description', config_name='extends')

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name="Sale Price")
    regular_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name="Regular Price")

    stock = models.PositiveIntegerField(default=0, null=True, blank=True)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, verbose_name="Shipping Amount")

    status = models.CharField(max_length=50, choices=STATUS, default="Published")
    featured = models.BooleanField(default=False, verbose_name="Marketplace Featured")

    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)

    sku = ShortUUIDField(length=5, max_length=50, alphabet="0123456789", unique=True, prefix="SKU-")
    slug = models.SlugField(null=True, blank=True)

    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-id']
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name
    
    def average_rating(self):
        return Review.objects.filter(product=self).aggregate(average_rating=models.Avg('rating'))['average_rating']
    
    def reviews(self):
        return Review.objects.filter(product=self)
    
    def gallery(self):
        return Gallery.objects.filter(product=self)
    
    def variants(self):
        return Variant.objects.filter(product=self)
    
    def vendor_order(self):
        return OrderItem.objects.filter(product=self, vendor=self.vendor)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) + '-' + str(shortuuid.uuid().lower()[:2])
        super(Product, self).save(*args, **kwargs)

class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, related_name="variants")
    name = models.CharField(max_length=1000, verbose_name="Variant Name", null=True, blank=True)

    def items(self):
        return VariantItem.objects.filter(variant=self)

    def __str__(self):
        return self.name
    
class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, verbose_name="Item Title", null=True, blank=True)
    content = models.CharField(max_length=1000, verbose_name="Item Content", null=True, blank=True)

    def __str__(self):
        return self.variant.name
    
class Gallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    image = models.ImageField(upload_to='images', default='gallery.png')
    gallery_id = ShortUUIDField(length=6, max_length=10, alphabet="0123456789", unique=True, prefix="GID-")

    def __str__(self):
        return f"{self.product.name} - image"
    
    class Meta:
        verbose_name_plural = "Gallery"
    
class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    cart_id = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cart_id} - {self.product.name}"

class Coupon(models.Model):
    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True)
    code = models.CharField(max_length=100)
    discount = models.IntegerField(default=1)

    def __str__(self):
        return self.code
    
class ShippingMethod(models.Model):
    vendor = models.ForeignKey(
        user_models.User,
        on_delete=models.CASCADE,
        related_name="shipping_methods"
    )
    name = models.CharField(max_length=100)  # e.g. "Standard", "Express"
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_days = models.PositiveIntegerField(default=3)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']
        unique_together = ('vendor', 'name')

    def __str__(self):
        return f"{self.vendor.username} - {self.name}"
    
class Order(models.Model):
    vendor = models.ManyToManyField(user_models.User, blank=True)
    customer = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer')
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default="Processing")
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHOD, default="None", null=True, blank=True)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default="Pending")
    initial_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Total amount before applying coupon")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Total amount saved by applying coupon")
    address = models.ForeignKey("customer.Address", on_delete=models.SET_NULL, null=True, blank=True)
    coupons = models.ManyToManyField(Coupon, blank=True)
    order_id = ShortUUIDField(length=6, max_length=25, alphabet="0123456789", unique=True, prefix="OID-")
    payment_id = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Order"

    def __str__(self):
        return self.order_id
    
    def order_items(self):
        return OrderItem.objects.filter(order=self)
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default="Pending")
    shipping_method = models.ForeignKey(
        ShippingMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items"
    )

    shipping_service = models.CharField(max_length=100, default="None", null=True, blank=True)
    tracking_id = models.CharField(max_length=100, default="None", null=True, blank=True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    color = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    initial_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Total amount before applying coupon")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Total amount saved by applying coupon")
    coupon = models.ManyToManyField(Coupon, blank=True)
    applied_coupon = models.BooleanField(default=False, help_text="Indicates if a coupon has been applied to this item")
    item_id = ShortUUIDField(length=6, max_length=25, alphabet="0123456789", unique=True, prefix="IID-")
    vendor = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, related_name="vendor_order_item")
    date = models.DateTimeField(default=timezone.now)

    def order_ids(self):
        return f"{self.order.order_id}"
    
    def __str__(self):
        return self.item_id
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Order Items"

class Review(models.Model):
    user = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews")
    review = models.TextField(null=True, blank=True)
    reply = models.TextField(null=True, blank=True)
    rating = models.IntegerField(choices=RATING, default=None)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        username = self.user.username if self.user else "Unknown User"
        product_name = self.product.name if self.product else "Unknown Product"
        return f"Review by {username} on {product_name}"