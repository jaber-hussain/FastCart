from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('', include('store.urls')),
    path('admin/', admin.site.urls),
    path('user/', include('userauths.urls')),
    path('customer/', include('customer.urls')),
    path('vendor/', include('vendor.urls')),
    path('manager/', include('manager.urls')),
    path('blog/', include('blog.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

# Serve static files (already handled by WhiteNoise in production)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ✅ Serve media files in both debug and production
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
