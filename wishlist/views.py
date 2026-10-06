from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Wishlist
from gallery.models import ImageWithCaption


@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, pk=item_id, is_active=True)
    if request.method != 'POST':
        return redirect(item.get_absolute_url())
    obj, created = Wishlist.objects.get_or_create(user=request.user, item=item)
    messages.success(request, f"'{item.caption}' was {'added to' if created else 'already in'} your wishlist.")
    return redirect(request.POST.get('next') or item.get_absolute_url())


@login_required
def remove_from_wishlist(request, item_id):
    item = get_object_or_404(ImageWithCaption, pk=item_id)
    if request.method == 'POST':
        Wishlist.objects.filter(user=request.user, item=item).delete()
        messages.success(request, f"Removed '{item.caption}' from your wishlist.")
    return redirect(request.POST.get('next') or 'wishlist:view_wishlist')


@login_required
def clear_wishlist(request):
    if request.method == 'POST':
        Wishlist.objects.filter(user=request.user).delete()
        messages.success(request, 'Your wishlist has been cleared.')
    return redirect('wishlist:view_wishlist')


@login_required
def view_wishlist(request):
    wishlist_entries = Wishlist.objects.filter(user=request.user).select_related('item', 'item__category')
    return render(request, 'view_wishlist.html', {'wishlist_items': wishlist_entries})
