from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files import File
from django.utils.text import slugify
from gallery.models import Category, ImageWithCaption

CATEGORIES = [
    ('Sofas & Seating', 'Sofas, lounge seating and everyday comfort pieces.'),
    ('Beds & Bedroom', 'Beds and bedroom furniture designed for restful spaces.'),
    ('Dining & Tables', 'Dining tables and practical table solutions for the home.'),
    ('Chairs', 'Dining, accent and utility chairs.'),
    ('Storage', 'Storage furniture for organized homes and workspaces.'),
    ('Custom Furniture', 'Furniture made around specific room sizes, finishes or requirements.'),
]

SAMPLE_PRODUCTS = [
    ('Heritage Teak Sofa', 34999, 'A warm teak-frame sofa with comfortable fabric seating, designed for everyday family rooms.', '210 × 85 × 90 cm', 'Teak wood, premium fabric', 'Natural teak', 'Sofas & Seating', '5 years'),
    ('Modern Lounge Sofa', 42999, 'Clean-lined contemporary seating for compact and open-plan living rooms.', '220 × 92 × 84 cm', 'Engineered wood, fabric', 'Stone beige', 'Sofas & Seating', '3 years'),
    ('Solid Wood Queen Bed', 38999, 'A sturdy queen-size bed with balanced proportions and a timeless wooden finish.', '160 × 200 × 105 cm', 'Solid wood', 'Walnut', 'Beds & Bedroom', '5 years'),
    ('Upholstered Storage Bed', 46999, 'A practical upholstered bed with integrated storage for bedrooms that need more room.', '180 × 200 × 110 cm', 'Engineered wood, upholstery', 'Olive grey', 'Beds & Bedroom', '3 years'),
    ('Family Dining Table', 31999, 'A generous dining table designed for daily meals, guests and weekend gatherings.', '180 × 90 × 76 cm', 'Sheesham wood', 'Honey brown', 'Dining & Tables', '5 years'),
    ('Everyday Dining Chair', 5499, 'Supportive dining chair with an easy-care finish and comfortable backrest.', '48 × 52 × 84 cm', 'Wood, fabric', 'Natural', 'Chairs', '2 years'),
    ('Tall Storage Cabinet', 24999, 'A versatile cabinet for books, linens, tableware and home essentials.', '90 × 45 × 180 cm', 'Engineered wood', 'Warm oak', 'Storage', '3 years'),
    ('Custom Study Table', 18999, 'A configurable work-from-home table for study rooms, bedrooms and compact offices.', 'Custom size', 'Wood, laminate', 'Choice of finish', 'Custom Furniture', '2 years'),
]

class Command(BaseCommand):
    help = 'Seed useful furniture categories and sample products for development/demo environments.'

    def handle(self, *args, **options):
        for name, description in CATEGORIES:
            Category.objects.update_or_create(name=name, defaults={'slug': slugify(name), 'description': description, 'is_active': True})
        created = 0
        static_dir = Path(__file__).resolve().parents[3] / 'static' / 'images'
        image_candidates = ['n3.jpg', 'n4.jpg', 'n5.jpg', 'n6.jpg', 'b1.jpg', 'b2.jpg', 'd1.jpg', 'd2.jpg']
        for idx, (caption, price, description, dimensions, materials, color, category_name, warranty) in enumerate(SAMPLE_PRODUCTS):
            category = Category.objects.get(name=category_name)
            product, was_created = ImageWithCaption.objects.get_or_create(caption=caption, defaults={
                'price': price, 'description': description, 'dimensions': dimensions, 'materials': materials,
                'color': color, 'category': category, 'stock_quantity': 20, 'is_active': True,
                'is_featured': idx < 4, 'warranty': warranty, 'lead_time': '2–3 weeks',
                'care_instructions': 'Use a soft dry cloth. Avoid prolonged moisture and direct heat.',
            })
            if was_created:
                created += 1
                candidate = static_dir / image_candidates[idx % len(image_candidates)]
                if candidate.exists():
                    with candidate.open('rb') as fh:
                        product.image.save(candidate.name, File(fh), save=True)
        self.stdout.write(self.style.SUCCESS(f'Catalog ready. Created {created} sample products.'))
