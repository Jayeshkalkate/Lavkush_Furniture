from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from gallery.models import ImageWithCaption
from .models import Wishlist
from django.shortcuts import render

@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    Wishlist.objects.get_or_create(user=request.user, item=item)
    return redirect('gallery')  # or use 'gallery:item_detail', etc.

@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    Wishlist.objects.filter(user=request.user, item=item).delete()
    return redirect('gallery')

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist/view_wishlist.html', {'wishlist_items': wishlist_items})
