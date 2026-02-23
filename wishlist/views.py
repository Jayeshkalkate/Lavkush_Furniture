from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from gallery.models import ImageWithCaption
from .models import Wishlist
from django.shortcuts import render
from datetime import timedelta, datetime
from django.utils.timezone import now

@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    Wishlist.objects.get_or_create(user=request.user, item=item)
    return redirect('gallery')

@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    Wishlist.objects.filter(user=request.user, item=item).delete()
    return redirect('gallery')


@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, "view_wishlist.html", {"wishlist_items": wishlist_items})


@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('item')

    for w in wishlist_items:
        w.item.is_new = w.item.uploaded_at >= (now() - timedelta(days=7))

    return render(request, "view_wishlist.html", {"wishlist_items": wishlist_items})
