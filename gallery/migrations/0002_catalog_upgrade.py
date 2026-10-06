from django.db import migrations, models
import cloudinary.models
import django.db.models.deletion
from django.db.models import Q
from django.utils.text import slugify


def backfill_product_catalog(apps, schema_editor):
    Product = apps.get_model('gallery', 'ImageWithCaption')
    Category = apps.get_model('gallery', 'Category')
    category_map = {}
    for name, desc in [
        ('Sofas & Seating', 'Sofas, lounge seating and everyday comfort pieces.'),
        ('Beds & Bedroom', 'Beds and bedroom furniture designed for restful spaces.'),
        ('Dining & Tables', 'Dining tables and practical table solutions for the home.'),
        ('Chairs', 'Dining, accent and utility chairs.'),
        ('Storage', 'Storage furniture for organized homes and workspaces.'),
        ('Custom Furniture', 'Furniture made around specific room sizes, finishes or requirements.'),
    ]:
        cat, _ = Category.objects.get_or_create(name=name, defaults={'slug': slugify(name), 'description': desc})
        category_map[name] = cat
    keywords = [
        ('sofa', 'Sofas & Seating'), ('couch', 'Sofas & Seating'), ('chair', 'Chairs'),
        ('bed', 'Beds & Bedroom'), ('table', 'Dining & Tables'), ('dining', 'Dining & Tables'),
        ('cabinet', 'Storage'), ('wardrobe', 'Storage'), ('storage', 'Storage'),
    ]
    for product in Product.objects.all().order_by('pk'):
        text = (product.caption or '').lower()
        category = next((category_map[v] for k, v in keywords if k in text), None)
        if category:
            product.category_id = category.pk
        base = slugify(product.caption or 'furniture')[:260] or 'furniture'
        slug = base
        n = 2
        while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
            slug = f'{base}-{n}'
            n += 1
        product.slug = slug
        product.sku = f'LF-{product.pk:05d}'
        product.price = product.price or 0
        product.description = product.description or ''
        product.dimensions = product.dimensions or ''
        product.materials = product.materials or ''
        product.save(update_fields=['category', 'slug', 'sku', 'price', 'description', 'dimensions', 'materials'])


class Migration(migrations.Migration):
    dependencies = [('gallery', '0001_initial'), ('account', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=120, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
            ],
            options={'ordering': ['name'], 'verbose_name_plural': 'Categories'},
        ),
        migrations.AddField(model_name='imagewithcaption', name='slug', field=models.SlugField(blank=True, db_index=True, max_length=280, null=True, unique=True)),
        migrations.AddField(model_name='imagewithcaption', name='sku', field=models.CharField(blank=True, db_index=True, max_length=80, null=True, unique=True)),
        migrations.AddField(model_name='imagewithcaption', name='updated_at', field=models.DateTimeField(auto_now=True, db_index=True)),
        migrations.AddField(model_name='imagewithcaption', name='category', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='gallery.category')),
        migrations.AddField(model_name='imagewithcaption', name='color', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='imagewithcaption', name='stock_quantity', field=models.PositiveIntegerField(default=20)),
        migrations.AddField(model_name='imagewithcaption', name='is_active', field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='imagewithcaption', name='is_featured', field=models.BooleanField(db_index=True, default=False)),
        migrations.AddField(model_name='imagewithcaption', name='warranty', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='imagewithcaption', name='lead_time', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='imagewithcaption', name='care_instructions', field=models.TextField(blank=True)),
        migrations.AddField(model_name='imagewithcaption', name='meta_title', field=models.CharField(blank=True, max_length=180)),
        migrations.AddField(model_name='imagewithcaption', name='meta_description', field=models.CharField(blank=True, max_length=320)),
        migrations.AlterField(model_name='imagewithcaption', name='image', field=cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image')),
        migrations.AlterModelOptions(name='imagewithcaption', options={'ordering': ['-is_featured', '-uploaded_at']}),
        migrations.AddField(model_name='rating', name='title', field=models.CharField(blank=True, max_length=160)),
        migrations.AddField(model_name='rating', name='review_text', field=models.TextField(blank=True)),
        migrations.AddField(model_name='rating', name='approved', field=models.BooleanField(db_index=True, default=True)),
        migrations.AddField(model_name='rating', name='updated_at', field=models.DateTimeField(auto_now=True)),
        migrations.AlterField(model_name='rating', name='rating', field=models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], default=5)),
        migrations.AlterUniqueTogether(name='rating', unique_together=set()),
        migrations.RunPython(backfill_product_catalog, migrations.RunPython.noop),
        migrations.AlterField(model_name='imagewithcaption', name='price', field=models.DecimalField(db_index=True, decimal_places=2, default=0, max_digits=10)),
        migrations.AlterField(model_name='imagewithcaption', name='description', field=models.TextField(blank=True)),
        migrations.AlterField(model_name='imagewithcaption', name='dimensions', field=models.CharField(blank=True, max_length=120)),
        migrations.AlterField(model_name='imagewithcaption', name='materials', field=models.CharField(blank=True, db_index=True, max_length=255)),
        migrations.AddConstraint(model_name='imagewithcaption', constraint=models.CheckConstraint(condition=Q(('price__gte', 0)), name='product_price_non_negative')),
        migrations.AddConstraint(model_name='rating', constraint=models.UniqueConstraint(fields=('user', 'item'), name='unique_user_product_rating')),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(blank=True, max_length=255, null=True, verbose_name='image')),
                ('alt_text', models.CharField(blank=True, max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='gallery.imagewithcaption')),
            ],
            options={'ordering': ['sort_order', 'created_at']},
        ),
    ]
