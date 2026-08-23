import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse

from .forms import UserForm, ProfileForm
from account.models import Items

logger = logging.getLogger(__name__)


def homepage(request):
    return render(request, 'index.html')


def aboutus(request):
    return render(request, 'aboutus.html')


def services(request):
    return render(request, 'services.html')


@login_required(login_url='login')
def contact(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()

        if not all([first_name, last_name, email, message]):
            messages.error(request, 'All fields are required.')
            return redirect('contactus')

        subject = f"New message from {first_name} {last_name}"
        full_message = f"Name: {first_name} {last_name}\nEmail: {email}\n\nMessage:\n{message}"
        try:
            send_mail(subject, full_message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            messages.success(request, 'Your message has been sent successfully.')
            logger.info(f"Contact email sent from {email}")
        except Exception as e:
            logger.error(f"Contact email failed: {e}")
            messages.error(request, 'Failed to send message. Please try again later.')
        return redirect('contactus')
    return render(request, 'contact.html')


@login_required(login_url='login')
def userprofile(request):
    user = request.user
    # Get profile info (Items from account app)
    profile = getattr(user, 'items', None)
    return render(request, 'userprofile.html', {'user': user, 'profile': profile})


@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    profile = getattr(user, 'items', None)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('userprofile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required(login_url='login')
def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)