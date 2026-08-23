import logging
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, Q
from django.core.files.base import ContentFile
from django.utils.text import slugify
import pandas as pd

from .models import ImageWithCaption, Rating
from .forms import ImageForm, FilterForm, BulkProductUploadForm

logger = logging.getLogger(__name__)


@staff_member_required
def bulk_upload_products(request):
    if request.method == "POST":
        form = BulkProductUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Invalid file format. Upload CSV or Excel.")
                return redirect("bulk_upload")

            required = ["caption", "price"]
            if not all(col in df.columns for col in required):
                messages.error(request, f"Missing required column: {', '.join(required)}")
                return redirect("bulk_upload")

            created_count = 0
            for _, row in df.iterrows():
                caption = row.get("caption")
                if not caption:
                    continue
                image_file = None
                image_url = row.get("image_url")
                if image_url:
                    try:
                        resp = requests.get(image_url, timeout=5)
                        if resp.status_code == 200:
                            safe_name = slugify(caption) + ".jpg"
                            image_file = ContentFile(resp.content, name=safe_name)
                    except Exception as e:
                        logger.warning(f"Image download failed for {caption}: {e}")

                ImageWithCaption.objects.create(
                    caption=caption,
                    price=row.get("price"),
                    description=row.get("description", ""),
                    dimensions=row.get("dimensions", ""),
                    materials=row.get("materials", ""),
                    image=image_file,
                )
                created_count += 1

            messages.success(request, f"{created_count} products uploaded successfully!")
            logger.info(f"Admin {request.user.username} bulk uploaded {created_count} products.")
            return redirect("gallery")
    else:
        form = BulkProductUploadForm()
    return render(request, "bulk_upload.html", {"form": form})


def gallery_view(request):
    images = ImageWithCaption.objects.annotate(
        avg_rating=Avg('ratings__rating')
    ).all()

    form = FilterForm(request.GET)
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        materials = form.cleaned_data.get('materials')
        sort_by = form.cleaned_data.get('sort_by')

        if keyword:
            images = images.filter(Q(caption__icontains=keyword) | Q(description__icontains=keyword))
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
            images = images.order_by('-avg_rating')

    # Round avg_rating for display
    for img in images:
        if img.avg_rating:
            img.avg_rating = round(img.avg_rating, 1)

    return render(request, 'gallery.html', {'images': images, 'form': form})


@login_required
def rate_item(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        if rating_value and rating_value.isdigit():
            rating_value = int(rating_value)
            if 1 <= rating_value <= 5:
                rating, created = Rating.objects.get_or_create(user=request.user, item=item)
                rating.rating = rating_value
                rating.save()
                messages.success(request, "Your rating has been submitted.")
                logger.info(f"User {request.user.username} rated item {item_id} with {rating_value}")
            else:
                messages.error(request, "Please select a rating between 1 and 5.")
        else:
            messages.error(request, "Invalid rating value.")
        return redirect('furniture_detail', item_id=item.id)

    # GET: show rating form
    rating = Rating.objects.filter(user=request.user, item=item).first()
    return render(request, 'rate_item.html', {'item': item, 'rating': rating})


def furniture_detail(request, item_id):
    item = get_object_or_404(ImageWithCaption.objects.annotate(
        avg_rating=Avg('ratings__rating')
    ), id=item_id)

    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(user=request.user, item=item).first()

    context = {
        'item': item,
        'rating_range': range(1, 6),
        'avg_rating': round(item.avg_rating, 1) if item.avg_rating else 0,
        'rating': user_rating,
    }
    return render(request, 'furniture_detail.html', context)


@user_passes_test(lambda u: u.is_superuser)
def upload_image(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Image uploaded successfully.")
            logger.info(f"Admin {request.user.username} uploaded a new image.")
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
            messages.success(request, "Image updated successfully.")
            logger.info(f"Admin {request.user.username} edited image {image_id}.")
            return redirect('gallery')
    else:
        form = ImageForm(instance=image)
    return render(request, 'edit_image.html', {'form': form, 'image': image})


@user_passes_test(lambda u: u.is_superuser)
def delete_image(request, image_id):
    image = get_object_or_404(ImageWithCaption, id=image_id)
    image.delete()
    messages.success(request, "Image deleted successfully.")
    logger.info(f"Admin {request.user.username} deleted image {image_id}.")
    return redirect('gallery')