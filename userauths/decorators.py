from django.core.exceptions import PermissionDenied
from functools import wraps

def manager_required(view_func):
    """
    Restrict access to manager users only.
    Assumes your User model has a boolean field `is_manager`.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login if not authenticated
            from django.shortcuts import redirect
            return redirect('userauths:login')

        if not getattr(request.user, 'is_manager', False):
            # Raise 403 if user is not a manager
            raise PermissionDenied("You are not authorized to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def vendor_required(view_func):
    """
    Restrict access to manager users only.
    Assumes your User model has a boolean field `is_vendor`.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login if not authenticated
            from django.shortcuts import redirect
            return redirect('userauths:login')

        if not getattr(request.user, 'is_vendor', False):
            # Raise 403 if user is not a vendor
            raise PermissionDenied("You are not authorized to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
