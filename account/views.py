from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Items

def register(request):  
    if request.method == "POST":
        full_name = request.POST["full_name"]
        email = request.POST["email"]
        phone_number = request.POST["phone_number"]
        address = request.POST["address"]
        city = request.POST["city"]
        username = request.POST["username"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = full_name
            user.save()

            # Save additional info to Items model
            Items.objects.create(user=user, phone_number=phone_number, address=address, city=city)

            messages.success(request, "Account has been created successfully")
            login(request, user)  # Automatically log in after registration
            return redirect("homepage")  # Redirect to homepage after login

    return render(request, "register.html")

def user_login(request):
    # If user is already logged in, redirect to the homepage
    if request.user.is_authenticated:
        return redirect('homepage')  # Redirect to main homepage if already logged in

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("homepage")  # Redirect to homepage after successful login
        else:
            messages.error(request, "Invalid Credentials")
    return render(request, "login.html")

def user_logout(request):
    logout(request)
    return redirect("login")  # Redirect to login page after logout

@login_required(login_url="login")
def home(request):
    items = Items.objects.filter(user=request.user)  # Show only the logged-in user's items
    return render(request, "index.html", {"items": items})
