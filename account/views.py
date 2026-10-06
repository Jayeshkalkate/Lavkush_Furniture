import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from .models import Items
from cart.views import merge_guest_cart

logger = logging.getLogger(__name__)


def _is_admin(user):
    return user.is_superuser


@user_passes_test(_is_admin)
def admin_user_list(request):
    users = User.objects.select_related('items').order_by('-date_joined')
    return render(request, 'admin_user_list.html', {'users': users})


@user_passes_test(_is_admin)
def delete_user(request, user_id):
    if request.method != 'POST':
        return redirect('admin_user_list')
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, 'You cannot delete your own account.')
    else:
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User {username} deleted successfully.')
    return redirect('admin_user_list')


def register(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        errors = []
        if not all([full_name, email, phone_number, address, city, username, password, confirm_password]):
            errors.append('Please complete every required field.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if User.objects.filter(username__iexact=username).exists():
            errors.append('Username already exists.')
        if email and User.objects.filter(email__iexact=email).exists():
            errors.append('Email already registered.')
        try:
            validate_password(password, User(username=username, email=email, first_name=full_name.split(' ')[0]))
        except Exception as exc:
            errors.extend(exc.messages)
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html', {'form_data': request.POST})

        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            parts = full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user.save(update_fields=['first_name', 'last_name'])
            Items.objects.update_or_create(user=user, defaults={
                'phone_number': phone_number,
                'address': address,
                'city': city,
            })
        merge_guest_cart(request, user)
        login(request, user)
        messages.success(request, 'Welcome to Lavkush Furniture. Your account is ready.')
        return redirect('homepage')
    return render(request, 'register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('homepage')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        locked_until = float(request.session.get('login_locked_until', 0) or 0)
        if timezone.now().timestamp() < locked_until:
            messages.error(request, 'Too many failed sign-in attempts. Please wait a few minutes and try again.')
        elif not username or not password:
            messages.error(request, 'Username and password are required.')
        else:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                request.session.pop('login_failures', None)
                request.session.pop('login_locked_until', None)
                login(request, user)
                merge_guest_cart(request, user)
                return redirect(request.GET.get('next') or 'homepage')
            failures = int(request.session.get('login_failures', 0) or 0) + 1
            request.session['login_failures'] = failures
            if failures >= 5:
                request.session['login_failures'] = 0
                request.session['login_locked_until'] = timezone.now().timestamp() + 180
                messages.error(request, 'Too many failed attempts. Sign-in is temporarily paused for 3 minutes.')
            else:
                messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')


def user_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been signed out safely.')
    return redirect('login')


@login_required
def home(request):
    return redirect('homepage')
