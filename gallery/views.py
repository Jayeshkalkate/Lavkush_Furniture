import io
import ipaddress
import logging
import socket
from urllib.parse import urlparse
import csv
from openpyxl import load_workbook
import requests
from PIL import Image as PILImage

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .forms import BulkProductUploadForm, FilterForm, ImageForm, ReviewForm
from .models import Category, ImageWithCaption, ProductImage, Rating

logger = logging.getLogger(__name__)


def _admin(user):
    return user.is_staff and user.is_active


def gallery_view(request):
    products = ImageWithCaption.objects.filter(is_active=True).select_related('category').annotate(avg_rating=Avg('ratings__rating', filter=Q(ratings__approved=True)))
    form = FilterForm(request.GET or None)
    if form.is_valid():
        keyword = form.cleaned_data.get('keyword')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        materials = form.cleaned_data.get('materials')
        category = form.cleaned_data.get('category')
        sort_by = form.cleaned_data.get('sort_by') or 'relevance'
        if keyword:
            products = products.filter(Q(caption__icontains=keyword) | Q(description__icontains=keyword) | Q(materials__icontains=keyword) | Q(category__name__icontains=keyword) | Q(color__icontains=keyword) | Q(sku__icontains=keyword))
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)
        if materials:
            products = products.filter(materials__icontains=materials)
        if category:
            products = products.filter(category=category)
        if sort_by == 'price_asc':
            products = products.order_by('price', 'caption')
        elif sort_by == 'price_desc':
            products = products.order_by('-price', 'caption')
        elif sort_by == 'latest':
            products = products.order_by('-uploaded_at')
        elif sort_by == 'rating':
            products = products.order_by('-avg_rating', '-uploaded_at')
        else:
            products = products.order_by('-is_featured', '-avg_rating', '-uploaded_at')

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.filter(is_active=True).annotate(product_count=Count('products', filter=Q(products__is_active=True)))
    query_params = request.GET.copy()
    query_params.pop('page', None)
    return render(request, 'gallery.html', {'products': page_obj, 'page_obj': page_obj, 'form': form, 'categories': categories, 'has_filters': bool(request.GET), 'query_string': query_params.urlencode()})


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = ImageWithCaption.objects.filter(is_active=True, category=category).select_related('category').annotate(avg_rating=Avg('ratings__rating', filter=Q(ratings__approved=True))).order_by('-is_featured', '-avg_rating', '-uploaded_at')
    page_obj = Paginator(products, 12).get_page(request.GET.get('page'))
    return render(request, 'category_detail.html', {'category': category, 'products': page_obj, 'page_obj': page_obj})


def furniture_detail(request, slug):
    item = get_object_or_404(ImageWithCaption.objects.filter(is_active=True).select_related('category').annotate(avg_rating=Avg('ratings__rating', filter=Q(ratings__approved=True))), slug=slug)
    reviews = item.ratings.filter(approved=True).select_related('user')
    user_rating = item.ratings.filter(user=request.user).first() if request.user.is_authenticated else None
    related = ImageWithCaption.objects.filter(is_active=True, category=item.category).exclude(pk=item.pk)[:4] if item.category_id else ImageWithCaption.objects.filter(is_active=True).exclude(pk=item.pk)[:4]
    context = {
        'item': item,
        'reviews': reviews,
        'related_products': related,
        'rating': user_rating,
        'review_form': ReviewForm(instance=user_rating) if request.user.is_authenticated else ReviewForm(),
        'avg_rating': round(item.avg_rating or 0, 1),
        'gallery_images': item.gallery_images.all(),
    }
    return render(request, 'furniture_detail.html', context)


@login_required
def rate_item(request, item_id):
    item = get_object_or_404(ImageWithCaption, pk=item_id, is_active=True)
    rating = Rating.objects.filter(user=request.user, item=item).first()
    if request.method != 'POST':
        return redirect(item.get_absolute_url())
    form = ReviewForm(request.POST, instance=rating)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.item = item
        obj.approved = True
        obj.save()
        messages.success(request, 'Thanks — your rating and review were saved.')
    else:
        messages.error(request, 'Please correct the review form and try again.')
    return redirect(item.get_absolute_url())


@user_passes_test(_admin)
def upload_image(request):
    form = ImageForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product published successfully.')
        return redirect('gallery')
    return render(request, 'upload.html', {'form': form})


@user_passes_test(_admin)
def edit_image(request, image_id):
    image = get_object_or_404(ImageWithCaption, pk=image_id)
    form = ImageForm(request.POST or None, request.FILES or None, instance=image)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('gallery')
    return render(request, 'edit_image.html', {'form': form, 'image': image})


@user_passes_test(lambda user: user.is_superuser)
def delete_image(request, image_id):
    if request.method != 'POST':
        return redirect('gallery')
    image = get_object_or_404(ImageWithCaption, pk=image_id)
    name = image.caption
    image.delete()
    messages.success(request, f"'{name}' was removed from the catalog.")
    return redirect('gallery')


def _safe_image_response(image_url):
    parsed = urlparse(str(image_url).strip())
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Image URL must use http or https.')
    host = parsed.hostname.lower()
    import django.conf
    allowlist = {h.lower() for h in django.conf.settings.BULK_IMAGE_ALLOWED_HOSTS}
    if not allowlist:
        raise ValueError('Remote image imports are disabled until BULK_IMAGE_ALLOWED_HOSTS is configured.')
    if host not in allowlist:
        raise ValueError('Image host is not in BULK_IMAGE_ALLOWED_HOSTS.')
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        for addr in addresses:
            ip = ipaddress.ip_address(addr[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                raise ValueError('Private or reserved image hosts are not allowed.')
    except socket.gaierror as exc:
        raise ValueError('Could not resolve image host.') from exc
    response = requests.get(str(image_url), timeout=(4, 8), allow_redirects=False, stream=True, headers={'User-Agent': 'LavkushFurnitureBulkImporter/1.0'})
    if response.status_code != 200:
        raise ValueError(f'Image download returned HTTP {response.status_code}.')
    content_type = (response.headers.get('Content-Type') or '').lower()
    if not content_type.startswith('image/'):
        raise ValueError('Downloaded content is not an image.')
    max_bytes = 5 * 1024 * 1024
    total = 0
    chunks = []
    for chunk in response.iter_content(64 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise ValueError('Image is larger than 5 MB.')
        chunks.append(chunk)
    data = b''.join(chunks)
    try:
        PILImage.MAX_IMAGE_PIXELS = 40_000_000
        img = PILImage.open(io.BytesIO(data))
        img.verify()
    except Exception as exc:
        raise ValueError('Downloaded file is not a valid image.') from exc
    return data


def _read_bulk(file):
    name = file.name.lower()
    rows = []
    if name.endswith('.csv'):
        text = file.read().decode('utf-8-sig')
        rows = list(csv.DictReader(io.StringIO(text)))
    elif name.endswith('.xlsx'):
        workbook = load_workbook(file, read_only=True, data_only=True)
        sheet = workbook.active
        values = list(sheet.iter_rows(values_only=True))
        if values:
            headers = [str(v or '').strip() for v in values[0]]
            for values_row in values[1:]:
                rows.append({headers[i]: values_row[i] if i < len(values_row) else '' for i in range(len(headers))})
    else:
        raise ValueError('Only CSV and XLSX files are supported.')
    return rows


@staff_member_required
def bulk_upload_products(request):
    form = BulkProductUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        file = request.FILES['file']
        if file.size > 10 * 1024 * 1024:
            form.add_error('file', 'Maximum file size is 10 MB.')
        else:
            try:
                rows = _read_bulk(file)
                if not rows:
                    raise ValueError('The import file has no data rows.')
                required = {'caption', 'price'}
                if not required.issubset({str(k).strip() for k in rows[0].keys()}):
                    raise ValueError('Required columns are: caption, price.')
                prepared = []
                for index, row in enumerate(rows, start=2):
                    caption = str(row.get('caption') or '').strip()
                    if not caption:
                        raise ValueError(f'Row {index}: caption is required.')
                    try:
                        price = Decimal(str(row.get('price') or 0).replace(',', '').strip())
                    except (TypeError, ValueError, InvalidOperation):
                        raise ValueError(f'Row {index}: price must be numeric.')
                    try:
                        stock_qty = int(float(row.get('stock_quantity') or 20))
                    except (TypeError, ValueError):
                        raise ValueError(f'Row {index}: stock_quantity must be a whole number.')
                    category_name = str(row.get('category') or '').strip()
                    if price < 0:
                        raise ValueError(f'Row {index}: price cannot be negative.')
                    image_data = None
                    image_url = str(row.get('image_url') or '').strip()
                    if image_url:
                        image_data = _safe_image_response(image_url)
                    prepared.append((row, caption, price, image_data, index, stock_qty, category_name))
                with transaction.atomic():
                    for row, caption, price, image_data, index, stock_qty, category_name in prepared:
                        category = None
                        if category_name:
                            category, _ = Category.objects.get_or_create(name=category_name, defaults={'slug': slugify(category_name) or 'category'})
                        product = ImageWithCaption.objects.create(
                            category=category,
                            caption=caption, price=price,
                            description=str(row.get('description') or '').strip(),
                            dimensions=str(row.get('dimensions') or '').strip(),
                            materials=str(row.get('materials') or '').strip(),
                            color=str(row.get('color') or '').strip(),
                            stock_quantity=max(0, stock_qty),
                            warranty=str(row.get('warranty') or '').strip(),
                            lead_time=str(row.get('lead_time') or '').strip(),
                            is_active=True,
                        )
                        if image_data:
                            product.image.save(f'{slugify(caption) or "product"}-{index}.jpg', ContentFile(image_data), save=True)
                messages.success(request, f'{len(prepared)} products imported successfully.')
                return redirect('gallery')
            except Exception as exc:
                logger.exception('Bulk import failed')
                messages.error(request, f'Import failed: {exc}')
    return render(request, 'bulk_upload.html', {'form': form})


@staff_member_required
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lavkush_product_import_sample.csv"'
    writer = csv.writer(response)
    writer.writerow(['caption', 'price', 'description', 'dimensions', 'materials', 'color', 'stock_quantity', 'warranty', 'lead_time', 'image_url', 'category'])
    writer.writerow(['Classic Teak Sofa', '34999', 'Hand-finished teak frame with comfortable fabric seating.', '210 x 85 x 90 cm', 'Teak wood, fabric', 'Natural wood', '10', '5 years', '2-3 weeks', '', 'Sofas & Seating'])
    return response
