from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .forms import ImageForm
from .models import ImageWithCaption
from django.contrib import messages

@user_passes_test(lambda u: u.is_superuser)  # Only allow admin users
def upload_image(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('gallery')
    else:
        form = ImageForm()
    return render(request, 'upload.html', {'form': form})

def gallery_view(request):
    images = ImageWithCaption.objects.all().order_by('-uploaded_at')
    return render(request, 'gallery.html', {'images': images})

@user_passes_test(lambda u: u.is_superuser)  # Only allow admin users
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
