from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import ImageWithCaption, Rating
from django.contrib import messages
from django.db.models import Avg
from .forms import ImageForm
from .forms import ImageForm, FilterForm

def gallery_view(request):
    images = ImageWithCaption.objects.all()
    form = FilterForm(request.GET)

    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        materials = form.cleaned_data.get('materials')
        sort_by = form.cleaned_data.get('sort_by')

        if keyword:
            images = images.filter(caption__icontains=keyword)
        if min_price is not None:
            images = images.filter(price__gte=min_price)
        if max_price is not None:
            images = images.filter(price__lte=max_price)
        if materials:
            images = images.filter(materials__icontains=materials)

        if sort_by == 'price_asc':
            images = images.order_by('price')
        elif sort_by == 'price_desc':
            images = images.order_by('-price')
        elif sort_by == 'latest':
            images = images.order_by('-uploaded_at')
        elif sort_by == 'oldest':
            images = images.order_by('uploaded_at')
        elif sort_by == 'rating':
            images = sorted(
                images,
                key=lambda i: Rating.objects.filter(item=i).aggregate(avg=Avg('rating'))['avg'] or 0,
                reverse=True
            )

    for image in images:
        image.avg_rating = int(round(Rating.objects.filter(item=image).aggregate(avg=Avg('rating'))['avg'] or 0))

    return render(request, 'gallery.html', {'images': images, 'form': form})

@login_required
def rate_item(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)

    rating, created = Rating.objects.get_or_create(user=request.user, item=item)

    if request.method == 'POST':
        rating_value = request.POST.get('rating')

        if rating_value:
            if int(rating_value) in range(1, 6):
                rating.rating = int(rating_value)
                rating.save()
                messages.success(request, "Your rating has been submitted.")
                return redirect('furniture_detail', item_id=item.id)
            else:
                messages.error(request, "Invalid rating. Please select a valid rating between 1 and 5.")
        else:
            rating.rating = 1
            rating.save()
            messages.warning(request, "You did not select a rating. A default rating of 1 has been applied.")
            return redirect('furniture_detail', item_id=item.id)

    return render(request, 'rate_item.html', {'item': item, 'rating': rating})


def furniture_detail(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    avg_rating = Rating.objects.filter(item=item).aggregate(Avg('rating'))['rating__avg'] or 0
    rating_range = range(1, 6)
    rating = None
    if request.user.is_authenticated:
        rating = Rating.objects.filter(user=request.user, item=item).first()

    return render(request, 'furniture_detail.html', {
        'item': item,
        'rating_range': rating_range,
        'avg_rating': avg_rating,
        'rating': rating,
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
