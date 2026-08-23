import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Items

logger = logging.getLogger(__name__)


@user_passes_test(lambda u: u.is_superuser)
def admin_user_list(request):
    users = User.objects.select_related('items').all()
    return render(request, 'admin_user_list.html', {'users': users})


@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)

    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        logger.info(f"Deleting user: {user_to_delete.username}")
        user_to_delete.delete()
        messages.success(request, f"User {user_to_delete.username} deleted successfully.")

    return redirect('admin_user_list')


def register(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not all([full_name, email, phone_number, address, city, username, password]):
            messages.error(request, "All fields are required.")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            # Split full name into first and last
            name_parts = full_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ""
            user.save()

            # Items will be created automatically by the post_save signal
            messages.success(request, "Account created successfully.")
            login(request, user)
            return redirect("homepage")  # ensure 'homepage' URL exists in project

    return render(request, "register.html")


def user_login(request):
    if request.user.is_authenticated:
        return redirect('homepage')

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, "login.html")

        logger.info(f"Login attempt for user: {username}")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.info(f"User {username} logged in successfully.")
            return redirect("homepage")
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, "Invalid credentials.")

    return render(request, "login.html")


def user_logout(request):
    logout(request)
    return redirect("login")


@login_required(login_url="login")
def home(request):
    # Since Items is a OneToOneField, we can access it directly.
    # If signal is active, every user has an Items instance.
    try:
        items = request.user.items
    except Items.DoesNotExist:
        items = None  # fallback, but shouldn't happen if signal works
    return render(request, "index.html", {"items": items})