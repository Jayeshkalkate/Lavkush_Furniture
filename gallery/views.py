from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import ImageWithCaption, Rating
from django.contrib import messages
from django.db.models import Avg
from .forms import ImageForm

def gallery_view(request):
    images = ImageWithCaption.objects.all().order_by('-uploaded_at')
    for image in images:
        image.avg_rating = int(round(Rating.objects.filter(item=image).aggregate(avg=Avg('rating'))['avg'] or 0))
    return render(request, 'gallery.html', {'images': images})

@login_required
def rate_item(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)

    rating, created = Rating.objects.get_or_create(user=request.user, item=item)

    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        if rating_value and int(rating_value) in range(1, 6):
            rating.rating = int(rating_value)
            rating.save()
            messages.success(request, "Your rating has been submitted.")
            return redirect('furniture_detail', item_id=item.id)
        else:
            messages.error(request, "Invalid rating. Please select a valid rating between 1 and 5.")

    return render(request, 'rate_item.html', {'item': item, 'rating': rating})

def furniture_detail(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    avg_rating = Rating.objects.filter(item=item).aggregate(Avg('rating'))['rating__avg'] or 0
    rating_range = range(1, 6)
    return render(request, 'furniture_detail.html', {
        'item': item,
        'rating_range': rating_range,
        'avg_rating': avg_rating,
    })

@user_passes_test(lambda u: u.is_superuser)
def upload_image(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gallery')
    else:
        form = ImageForm()
    return render(request, 'upload.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def edit_image(request, image_id):
    image = get_object_or_404(ImageWithCaption, id=image_id)
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES, instance=image)
        if form.is_valid():
            form.save()
            return redirect('gallery')
    else:
        form = ImageForm(instance=image)
    return render(request, 'edit_image.html', {'form': form, 'image': image})

@user_passes_test(lambda u: u.is_superuser)
def delete_image(request, image_id):
    image = get_object_or_404(ImageWithCaption, id=image_id)
    image.delete()
    messages.success(request, "Image deleted successfully.")
    return redirect('gallery')
