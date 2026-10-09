import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import validate_email
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from .forms import ProfileForm, UserForm
from account.models import Items
from gallery.models import ImageWithCaption, Category

logger = logging.getLogger(__name__)


def homepage(request):
    featured = ImageWithCaption.objects.filter(is_active=True, is_featured=True).select_related('category').order_by('-uploaded_at')[:8]
    if not featured:
        featured = ImageWithCaption.objects.filter(is_active=True).select_related('category').order_by('-uploaded_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(request, 'index.html', {'featured_products': featured, 'categories': categories})


def healthz(request):
    """DB-free health check for Render and the wake-up loader page.

    The CORS header lets the static loader (another origin) read the answer; while the
    service is asleep Render replies without it, so the loader simply keeps waiting.
    """
    response = JsonResponse({'status': 'ok'})
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'no-store'
    return response


def aboutus(request):
    return render(request, 'aboutus.html')


def services(request):
    return render(request, 'services.html')


def contact(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        honeypot = request.POST.get('website', '').strip()
        if honeypot:
            return redirect('contactus')
        if not all([first_name, email, message]):
            messages.error(request, 'Please fill in your name, email and message.')
            return redirect('contactus')
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address.')
            return redirect('contactus')
        first_name, last_name, message = first_name[:100], last_name[:100], message[:5000]
        if '\n' in email or '\r' in email:
            return redirect('contactus')
        try:
            mail = EmailMessage(f'New website enquiry from {first_name} {last_name}'.strip(), f'Name: {first_name} {last_name}\nEmail: {email}\n\nMessage:\n{message}', settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL], reply_to=[email])
            mail.send(fail_silently=False)
            messages.success(request, 'Thanks — your message has been sent. We will get back to you soon.')
        except Exception:
            logger.exception('Contact message failed')
            messages.error(request, 'We could not send your message right now. Please call or email us directly.')
        return redirect('contactus')
    return render(request, 'contact.html')


@login_required
def userprofile(request):
    profile = getattr(request.user, 'items', None)
    return render(request, 'userprofile.html', {'profile': profile})


@login_required
def edit_profile(request):
    user = request.user
    profile, _ = Items.objects.get_or_create(user=user, defaults={'phone_number': '', 'address': '', 'city': ''})
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save(); profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('userprofile')
        messages.error(request, 'Please correct the highlighted fields.')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)
