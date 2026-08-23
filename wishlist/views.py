import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from datetime import timedelta
from gallery.models import ImageWithCaption
from .models import Wishlist

logger = logging.getLogger(__name__)


@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    obj, created = Wishlist.objects.get_or_create(user=request.user, item=item)
    if created:
        logger.info(f"User {request.user.username} added item {item.id} to wishlist.")
        messages.success(request, f"Added '{item.caption}' to wishlist.")
    else:
        messages.info(request, f"'{item.caption}' is already in your wishlist.")
    return redirect('gallery')


@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, id=item_id)
    deleted, _ = Wishlist.objects.filter(user=request.user, item=item).delete()
    if deleted:
        logger.info(f"User {request.user.username} removed item {item.id} from wishlist.")
        messages.success(request, f"Removed '{item.caption}' from wishlist.")
    else:
        messages.warning(request, "Item was not in your wishlist.")
    return redirect('gallery')


@login_required
def view_wishlist(request):
    # Fetch wishlist items with related item data
    wishlist_entries = Wishlist.objects.filter(user=request.user).select_related('item')

    # Annotate each item with is_new flag (if uploaded within 7 days)
    seven_days_ago = now() - timedelta(days=7)
    for entry in wishlist_entries:
        entry.item.is_new = entry.item.uploaded_at >= seven_days_ago

    return render(request, "view_wishlist.html", {"wishlist_items": wishlist_entries})