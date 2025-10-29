from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from userauths.forms import UserRegisterForm
from userauths import forms as userauths_forms
from userauths import models as userauths_models
from vendor import models as vendor_models
from django.contrib.auth import authenticate, logout as auth_logout, login as auth_login

# Create your views here.
def register(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already registered and logged in.')
        return redirect('/')

    form = userauths_forms.UserRegisterForm(request.POST or None)
    if form.is_valid():
        # 1. create user
        user = form.save(commit=False)
        user.save()
        full_name = form.cleaned_data.get('full_name')
        user_type = form.cleaned_data.get('user_type')

        # 2. profile
        profile = userauths_models.Profile.objects.create(
            user=user,
            full_name=full_name,
            mobile=form.cleaned_data.get('mobile'),
            user_type=user_type,
            birth_date=form.cleaned_data.get('birth_date'),
            cnic=form.cleaned_data.get('cnic'),
            security_question=form.cleaned_data.get('security_question'),
            security_answer=form.cleaned_data.get('security_answer')
        )

        # 3. vendor vs customer
        if user_type == 'Vendor':
            vendor_models.Vendor.objects.create(
                user=user,
                store_name=full_name,
                is_approved=False          # waiting for manager
            )
            messages.info(request,
                'Your vendor account has been created and is waiting for manager approval.')
            # Do NOT log vendor in yet
            return redirect('userauths:login')

        # ---------- customer ----------
        profile.user_type = 'Customer'
        profile.save()
        user = authenticate(email=user.email, password=form.cleaned_data.get('password1'))
        auth_login(request, user)
        messages.success(request, f'Account created for {full_name}. You are now logged in!')
        return redirect(request.GET.get('next', 'store:index'))

    else:
        messages.warning(request, "Please correct the errors below.")
        print("FORM ERRORS:", form.errors)

    return render(request, 'userauths/sign-up.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        messages.warning(request, 'You are already logged in.')
        return redirect('/')

    if request.method == 'POST':
        form = userauths_forms.LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            user = authenticate(email=email, password=password)
            if user:
                # ---------- unified admission gate ----------
                from vendor.models import Vendor
                is_customer = (
                    hasattr(user, 'profile') and
                    user.profile.user_type == 'Customer'
                )
                is_approved_vendor = Vendor.objects.filter(
                    user=user, is_approved=True
                ).exists()

                if not (is_customer or is_approved_vendor):
                    messages.warning(
                        request,
                        'Your vendor account has been rejected.'
                    )
                    return redirect('userauths:login')
                # --------------------------------------------
                auth_login(request, user)
                messages.success(request, "You are now logged in!")
                return redirect(request.GET.get('next', 'store:index'))
            else:
                messages.error(request, "Email or password is incorrect.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = userauths_forms.LoginForm()

    return render(request, 'userauths/sign-in.html', {'form': form})

    
def user_logout(request):
    if not request.user.is_authenticated:
        messages.warning(request, 'You are not logged in.')
        return redirect("userauths:login")
    cart_id = request.session.get('cart_id')

    auth_logout(request)
    if cart_id:
        request.session['cart_id'] = cart_id
    messages.success(request, "You have been logged out.")
    return redirect("userauths:login")

def reset_password_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = userauths_models.User.objects.get(email=email)
            # Store user id in session for next step
            request.session['reset_user_id'] = user.id
            return redirect('userauths:reset_password_security')
        except userauths_models.User.DoesNotExist:
            messages.error(request, "No user found with this email.")
    return render(request, 'userauths/password/reset_password_request.html')

def reset_password_security(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('userauths:reset_password_request')
    
    user = userauths_models.User.objects.get(id=user_id)
    profile = user.profile  # assuming OneToOneField related_name="user_profile"

    if request.method == 'POST':
        answer = request.POST.get('security_answer')
        if answer and answer.strip().lower() == profile.security_answer.lower():
            # Answer correct, go to set new password
            return redirect('userauths:set_new_password')
        else:
            messages.error(request, "Security answer is incorrect.")

    context = {
        'security_question': profile.security_question
    }
    return render(request, 'userauths/password/reset_password_security.html', context)

from django.contrib.auth.hashers import make_password

def set_new_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('userauths:reset_password_request')
    
    user = userauths_models.User.objects.get(id=user_id)

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 and password1 == password2:
            user.password = make_password(password1)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            # Clean session
            request.session.pop('reset_user_id', None)
            return redirect('userauths:login')
        else:
            messages.error(request, "Passwords do not match.")

    return render(request, 'userauths/password/set_new_password.html')
