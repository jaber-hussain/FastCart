<div align="center">

# FastCart 🛒

**Multi-Vendor Ecommerce Platform - Built with Django**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat-square&logo=django&logoColor=white)](https://djangoproject.com)
[![Celery](https://img.shields.io/badge/Celery-Async_Tasks-37814A?style=flat-square&logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://opensource.org/licenses/MIT)

> FastCart is a full-featured multi-vendor ecommerce web platform where multiple vendors can register, manage their stores, and sell products - while customers shop, track orders, and manage their accounts.

</div>

---

## 🌐 What is FastCart?

FastCart is a **server-side rendered Django ecommerce platform** - no separate frontend framework, just clean Django + HTML templates. It supports three user roles: **Customer**, **Vendor**, and **Manager (Admin)**, each with their own dedicated dashboard and workflows.

---

## ✨ Features

### 👤 Customer
- Browse products by category with filters
- Product detail with image gallery and variants (size, color, etc.)
- Cart and checkout flow
- Multiple saved addresses
- Wishlist management
- Order tracking with status timeline
- Order and order item detail views
- Notifications dashboard
- Profile management with CNIC and birth date
- Password change and reset (security questions flow)
- Payment via **JazzCash**, **Easypaisa**, **Credit Card**, and **Cash on Delivery**

### 🏪 Vendor
- Vendor registration with approval workflow
- Dedicated vendor dashboard
- Create and manage product listings with variants and image gallery
- Coupon management
- Order and order item management
- Customer reviews overview
- Notification system
- Profile and password management

### 🛠️ Manager (Super Admin)
- Full admin dashboard
- Vendor management - add, edit, approve, view vendors
- Customer management - view and manage customers
- Product management - edit and manage all products
- Order management - view, edit, manage all orders
- Category management - add, edit, view categories
- Blog management - add, edit, manage blog posts and comments
- Audit trail visibility

---

## 🏗️ Project Structure

```
├── audit/             # Audit logging - middleware, signals, models
│                      # tracks user actions across the platform
├── blog/              # Blog with categories, posts, comments
├── customer/          # Customer profile, addresses, wishlist,
│                      # notifications, orders, context processors
├── store/             # Core ecommerce - products, variants, gallery,
│                      # cart, checkout, orders, shipping methods,
│                      # payment status, order tracker, Celery tasks
├── vendor/            # Vendor profiles, products, orders,
│                      # coupons, reviews, dashboard
├── userauths/         # Auth - sign in, sign up, password reset
│                      # (security question flow), decorators, forms
├── manager/           # Manager admin panel - vendors, customers,
│                      # orders, products, categories, blog, comments
│
└── plugin/            # Utility modules
    ├── countries.py         # Country list for addresses
    ├── exchange_rate.py     # Currency exchange rate handling
    ├── paginate_queryset.py # Reusable pagination helper
    ├── service_fee.py       # Platform service fee calculation
    └── tax_calculation.py   # Tax calculation logic
```

---

## 🔌 Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.x |
| Task Queue | Celery |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Frontend | Django Templates + Bootstrap + jQuery |
| UI Plugins | Slick Slider, Ion Range Slider, Lightbox |
| Email | HTML email templates (order notifications) |
| Payments | JazzCash, Easypaisa, Credit Card, Cash on Delivery |
| Testing | pytest |

---

## 🔑 Key Technical Highlights

### 🏪 Multi-Vendor Architecture
- Each vendor has an independent dashboard to manage their own products, orders, and coupons
- Vendor approval workflow - vendors must be approved by the manager before going live
- Vendor-specific order and review management

### 📦 Product System
- Products support **variants** (e.g. size, color) with variant items
- Image gallery per product
- Category-based browsing with filters
- Coupon system for discounts

### 🚚 Order & Shipping
- Shipping method management per order item
- Order tracker page for customers to follow order status
- Email notifications to both customer and vendor on new orders (HTML + plain text templates)
- Celery async tasks for background order processing

### 💰 Payments
- JazzCash and Easypaisa integration
- Credit card and Cash on Delivery support
- Payment status page

### 📊 Audit System
- Full audit trail via middleware and signals
- Tracks user actions across the platform for accountability

### 🌍 Platform Utilities
- Exchange rate support for multi-currency
- Tax calculation module
- Service fee calculation
- Reusable pagination helper used across all list views

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Redis (for Celery broker)

### Setup

```bash
# Clone the repo
git clone https://github.com/jaber-hussain/fastcart.git
cd fastcart

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Fill in DB, email, and payment credentials

# Run migrations
python manage.py migrate

# Load sample blog data (optional)
python manage.py loaddata data/blog_post.json

# Start development server
python manage.py runserver

# Start Celery worker (separate terminal)
celery -A ecom_proj worker --loglevel=info
```

---

## 📄 Pages & Templates

| Section | Pages |
|---|---|
| Store | Home, Shop, Categories, Product Detail, Cart, Checkout, Order Tracker, Payment Status |
| Customer | Dashboard, Orders, Order Detail, Wishlist, Addresses, Notifications, Profile |
| Vendor | Dashboard, Products, Orders, Coupons, Reviews, Profile |
| Manager | Dashboard, Vendors, Customers, Orders, Products, Categories, Blog |
| Auth | Sign In, Sign Up, Password Reset (security question flow) |
| Blog | Blog List, Blog Detail |
| Pages | About, Contact, FAQs, Privacy Policy, Terms & Conditions |

---

## 👨‍💻 Author

**Jaber Hussain**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/jaber-hussain/)
[![Fiverr](https://img.shields.io/badge/Fiverr-1DBF73?style=flat-square&logo=fiverr&logoColor=white)](https://www.fiverr.com/jaberhussain503)
[![Email](https://img.shields.io/badge/Email-EA4335?style=flat-square&logo=gmail&logoColor=white)](mailto:jaberchaudary@gmail.com)

---

<div align="center">

*Built with ❤️ using Django*

</div>
