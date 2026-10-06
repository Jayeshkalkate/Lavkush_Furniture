"""Import the shop's own furniture photos as products.

Usage:
    python manage.py import_catalog            # add missing products
    python manage.py import_catalog --update   # also refresh details/prices of existing ones

Photos live in  catalog_data/images/.  Edit the PRODUCTS list below
(names, prices, materials...) or edit products later in the Django admin.
PRICES ARE PLACEHOLDERS - set your real prices before going live.
"""
from pathlib import Path

from django.conf import settings
import cloudinary.uploader
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from gallery.models import Category, ImageWithCaption

CATEGORIES = {
    'Beds & Bedroom': 'Custom-made beds with storage, headboards and matching side tables.',
    'Wooden Doors': 'Handcrafted main doors and room doors in teak and wood finishes.',
    'TV Units': 'Wall-mounted TV panels and TV cabinets with storage and ambient lighting.',
}

BED_CARE = 'Wipe with a soft dry cloth. Avoid water spills and direct sunlight on laminate and upholstery.'
DOOR_CARE = 'Dust with a soft cloth. Re-polish every 1-2 years. Keep away from standing water and termites.'
TV_CARE = 'Wipe with a soft dry cloth. Do not place hot items on laminate. Keep LED strips dust-free.'

# (image file, name, category, price, description, materials, color, warranty, lead time)
BEDS = [
    ('b1.jpg', 'Floating Platform Bed with LED Headboard Ledge', 42000, 'Low platform bed with a floating headboard panel, built-in display ledge with warm LED lighting and a clean wooden base. Pairs well with a matching sliding wardrobe.', 'Plywood, laminate, veneer', 'Oak and white', 'Light oak and cream'),
    ('b5.jpg', 'Geometric Panel Headboard Bed', 38000, 'Double bed with a bold geometric headboard in walnut and white laminate and a sturdy platform base.', 'Plywood, laminate', 'Walnut and white', 'Walnut and white'),
    ('b6.jpg', 'Storage Platform Bed with LED Underglow', 46000, 'Raised-edge platform bed with drawer storage and soft LED underglow, designed for a modern bedroom.', 'Plywood, laminate, LED lighting', 'Maroon and white', 'Maroon and white'),
    ('b9.jpg', 'King Bed with Tufted Headboard and Side Tables', 52000, 'King-size bed with a tufted white leatherette headboard, attached side tables and a light oak finish with black accents.', 'Plywood, laminate, leatherette', 'Light oak and black', 'Light oak and black'),
    ('b10.jpg', 'Cushion Panel Headboard Bed', 44000, 'Double bed with a padded leatherette panel headboard, bedside table with drawers and a solid platform frame.', 'Plywood, laminate, leatherette', 'Brown and cream', 'Brown and cream'),
    ('b11.jpg', 'Low Platform Bed with Wall Panel', 48000, 'Low-profile bed with a full-width headboard wall panel and integrated side tables for a clutter-free look.', 'Plywood, laminate', 'Walnut and white', 'Walnut and white'),
    ('b13.jpg', 'Designer Bed with Square Frame Headboard', 43000, 'Bed with a black and white headboard featuring square frame accents, spotlight niche and attached side units.', 'Plywood, laminate', 'Black and white', 'Black and white'),
    ('b16.jpg', 'Drawer Storage Bed', 36000, 'Practical white bed with a built-in storage drawer and a walnut headboard panel.', 'Plywood, laminate', 'White and walnut', 'White and walnut'),
    ('b17.jpg', 'Panel Headboard Bed with Open Shelf', 41000, 'Double bed with a layered walnut and white panel headboard, open display shelf and attached side table.', 'Plywood, laminate', 'Walnut and white', 'Walnut and white'),
    ('b18.jpg', 'Tall Tufted Headboard Bed', 49000, 'Statement bed with a tall tufted white headboard flanked by patterned side panels and matching side tables.', 'Plywood, laminate, leatherette', 'White and brown', 'White and brown'),
]

DOORS = [
    ('d1.jpg', 'Teak Main Door with Glass Panes and Side Panel', 28000, 'Solid panel main door with a fixed side panel and nine small frosted-glass panes for light without losing privacy.', 'Teak wood, frosted glass', 'Dark teak polish'),
    ('d2.jpg', 'Double-Leaf Arch Panel Main Door', 32000, 'Double-leaf main door with raised arch-style panels, dark walnut finish and a lever handle.', 'Teak wood', 'Dark walnut'),
    ('d3.jpg', 'Teak Door with Vertical Glass Panes', 24000, 'Teak door with five vertical frosted-glass panes and geometric raised panels.', 'Teak wood, frosted glass', 'Natural teak'),
    ('d4.jpg', 'Carved Teak Door with Slat Design', 30000, 'Hand-carved door combining a horizontal slat feature with floral roundel carvings.', 'Teak wood', 'Natural light teak'),
    ('d5.jpg', 'Premium Double Door with Brass Grille', 55000, 'Premium double door in dark mahogany finish with decorative brass-tone grille, glass inserts and carved panels.', 'Hardwood, brass-finish metal, glass', 'Dark mahogany'),
    ('d6.jpg', 'Six-Panel Flush Room Door', 14000, 'Clean six-panel room door with a rich walnut veneer finish and lever handle.', 'Engineered wood, veneer', 'Walnut'),
    ('d7.jpg', 'Teak Grid Panel Door with Brass Studs', 27000, 'Teak door with a grid pattern of raised panels and brass stud detailing.', 'Teak wood, brass studs', 'Natural teak'),
    ('d8.jpg', 'Glossy Teak Double Door with Diamond Panels', 34000, 'Double door with diamond-shaped raised panels, glossy teak polish and steel handles.', 'Teak wood, stainless steel', 'Glossy golden teak'),
    ('d9.jpg', 'Teak Door with Swastik Motif Panel', 26000, 'Teak door with an auspicious Swastik motif inside a square carved frame and nine raised panels below.', 'Teak wood', 'Natural teak'),
    ('d10.jpg', 'Ornate Carved Double Door with Glass Jali', 62000, 'Richly carved double door with scrollwork top, decorative glass jali panels and brass handle. A showpiece entrance.', 'Hardwood, glass, brass', 'Antique brown'),
    ('d11.jpg', 'Polished Teak Double Door with Steel Handles', 36000, 'Double door with raised panels, decorative metal inlay and long steel handles in a deep polished teak finish.', 'Teak wood, stainless steel', 'Polished teak'),
    ('d12.jpg', 'Sunburst Arch Carved Door with Om Motif', 29000, 'Carved door with a sunburst arch, Om motif and pyramid raised panels.', 'Teak wood', 'Natural light teak'),
    ('d13.jpg', 'Pyramid Panel Door with Steel Inlay', 31000, 'Walnut-tone door with pyramid raised panels and a decorative centre inlay.', 'Teak wood, metal inlay', 'Walnut'),
    ('d14.jpg', 'Sunburst Arch Pyramid Panel Door', 28500, 'Light teak door with sunburst arch carving and pyramid panels for a traditional look.', 'Teak wood', 'Natural light teak'),
    ('d15.jpg', 'Slat Centre Pyramid Panel Door', 27500, 'Door with a slatted centre feature and pyramid panels in a grey-brown wood finish.', 'Teak wood', 'Grey-brown'),
    ('d16.jpg', 'Carved Centre Motif Pyramid Door', 28000, 'Door with a vertical carved centre motif framed by pyramid panels in a washed wood finish.', 'Teak wood', 'Washed brown'),
]

TVS = [
    ('n1.jpg', 'Marble Look TV Wall Unit with Display Niches', 58000, 'Full TV wall with marble-effect panel, backlit edge, six square display niches and a floating storage cabinet.', 'Plywood, laminate, marble-effect panel, LED', 'White and black'),
    ('n2.jpg', 'TV Unit with Glass Display Cabinet', 46000, 'Floor-standing TV unit with a lit glass display cabinet, stone-effect back panel and closed storage below.', 'Plywood, laminate, glass', 'Brown and white'),
    ('n3.jpg', 'Wall Mounted TV Panel with Low Console', 40000, 'Minimal TV wall with an angled white panel, wooden accents and a long floating console with storage.', 'Plywood, laminate', 'White and walnut'),
    ('n4.jpg', 'Backlit TV Wall with Open Shelf Tower', 52000, 'Textured wallpaper TV wall with warm LED backlight, open shelf tower and low drawer console.', 'Plywood, laminate, LED', 'Cream, brown and black'),
    ('n5.jpg', 'Modern TV Unit with Blue LED Niches', 44000, 'Contemporary TV panel with three LED display niches, white slat panel and a stepped floating console.', 'Plywood, laminate, LED', 'Brown and white'),
    ('n6.jpg', 'TV Cabinet with Glass Shelves and LED', 48000, 'TV cabinet with drawers, glass shelves and blue LED accents on a dark panel wall.', 'Plywood, laminate, glass, LED', 'Black and white'),
    ('n7.jpg', 'Wood Finish TV Wall Panel with Low Console', 38000, 'Large wood-finish TV back panel with side shelf unit and a low console with drawers.', 'Plywood, laminate', 'Oak and white'),
    ('n8.jpg', 'Designer TV Unit with Spot Niches and Cove Light', 56000, 'Designer TV wall with lit display niches, cove lighting and a floating console in white and brown.', 'Plywood, laminate, LED', 'White and dark brown'),
    ('n9.jpg', 'Striped Wood TV Wall Unit', 42000, 'Striped wood panel TV wall with a white feature panel, side shelf units and a low console.', 'Plywood, laminate', 'Dark brown and white'),
    ('n10.jpg', 'Full Height TV Wall with Wall Niches', 45000, 'Full-height wood-finish TV wall with open wall niches and a low floating console in white and brown.', 'Plywood, laminate', 'Brown and white'),
]


def build_products():
    for f, name, price, desc, mat, color, *rest in BEDS:
        yield dict(file=f, name=name, cat='Beds & Bedroom', price=price, desc=desc, mat=mat, color=color,
                   dims='Custom size (single, queen or king)', warranty='2 years on workmanship', lead='2-3 weeks', care=BED_CARE)
    for f, name, price, desc, mat, color in DOORS:
        yield dict(file=f, name=name, cat='Wooden Doors', price=price, desc=desc, mat=mat, color=color,
                   dims='Made to measure (standard 7 x 3 ft)', warranty='5 years on workmanship', lead='2-4 weeks', care=DOOR_CARE)
    for f, name, price, desc, mat, color in TVS:
        yield dict(file=f, name=name, cat='TV Units', price=price, desc=desc, mat=mat, color=color,
                   dims='Made to measure for your wall', warranty='2 years on workmanship', lead='2-3 weeks', care=TV_CARE)


class Command(BaseCommand):
    help = 'Import the shop furniture photos from catalog_data/images as products.'

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store_true', help='Update details of products that already exist.')

    def handle(self, *args, **opts):
        img_dir = Path(settings.BASE_DIR) / 'catalog_data' / 'images'
        cats = {}
        for name, desc in CATEGORIES.items():
            cats[name], _ = Category.objects.update_or_create(name=name, defaults={'slug': slugify(name), 'description': desc, 'is_active': True})
        created = updated = skipped = 0
        counters = {}
        for p in build_products():
            path = img_dir / p['file']
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"Missing image {p['file']} - skipped"))
                skipped += 1
                continue
            counters[p['cat']] = counters.get(p['cat'], 0) + 1
            details = dict(price=p['price'], description=p['desc'], dimensions=p['dims'], materials=p['mat'], color=p['color'],
                           category=cats[p['cat']], stock_quantity=10, is_active=True, is_featured=counters[p['cat']] <= 2,
                           warranty=p['warranty'], lead_time=p['lead'], care_instructions=p['care'],
                           meta_title=f"{p['name']} | Lavkush Furniture Nandurbar",
                           meta_description=p['desc'][:300])
            product, was_created = ImageWithCaption.objects.get_or_create(caption=p['name'], defaults=details)
            if was_created:
                created += 1
            elif opts['update']:
                for k, v in details.items():
                    setattr(product, k, v)
                product.save()
                updated += 1
            if not product.image:
                if not settings.USE_CLOUDINARY:
                    self.stdout.write(self.style.WARNING(f"{p['name']}: Cloudinary keys missing in .env - created without image."))
                    continue
                try:
                    res = cloudinary.uploader.upload(str(path), folder='lavkush/catalog', public_id=path.stem, overwrite=True)
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"{p['name']}: image upload failed: {exc}"))
                    continue
                product.image = f"{res['resource_type']}/{res['type']}/v{res['version']}/{res['public_id']}.{res['format']}"
                product.save(update_fields=['image'])
        self.stdout.write(self.style.SUCCESS(f'Done. Created {created}, updated {updated}, skipped {skipped}.'))