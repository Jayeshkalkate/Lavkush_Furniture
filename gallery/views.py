from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from .models import ImageWithCaption, Rating
from django.contrib import messages
from django.db.models import Avg
from .forms import ImageForm
from .forms import ImageForm, FilterForm
import pandas as pd
from .forms import BulkProductUploadForm
from django.contrib.admin.views.decorators import staff_member_required
import requests
from django.core.files.base import ContentFile
from django.utils.text import slugify

@staff_member_required
def bulk_upload_products(request):
    if request.method == "POST":
        form = BulkProductUploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES["file"]

            # Check file type
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                messages.error(request, "Invalid file format. Upload CSV or Excel.")
                return redirect("bulk_upload")

            # Optional: Check required columns
            required_columns = ["caption", "price"]
            for col in required_columns:
                if col not in df.columns:
                    messages.error(request, f"Missing required column: {col}")
                    return redirect("bulk_upload")

            for _, row in df.iterrows():
                image_file = None

                caption = row.get("caption")
                price = row.get("price")
                description = row.get("description")
                dimensions = row.get("dimensions")
                materials = row.get("materials")
                image_url = row.get("image_url")

                # Skip rows without caption (important for NOT NULL field)
                if not caption:
                    continue

                # Download image if URL exists
                if image_url:
                    try:
                        response = requests.get(image_url, timeout=5)
                        if response.status_code == 200:
                            safe_caption = slugify(caption)
                            file_name = f"{safe_caption}.jpg"
                            image_file = ContentFile(response.content, name=file_name)
                    except Exception as e:
                        print("Image download failed:", e)

                # Final safe caption
                final_caption = caption or "No Caption"

                ImageWithCaption.objects.create(
                    caption=final_caption,
                    price=price,
                    description=description,
                    dimensions=dimensions,
                    materials=materials,
                    image=image_file,
                )

            messages.success(request, "Products uploaded successfully with images!")
            return redirect("gallery")

    else:
        form = BulkProductUploadForm()

    return render(request, "bulk_upload.html", {"form": form})


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
