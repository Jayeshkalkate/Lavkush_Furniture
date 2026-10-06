# Lavkush Furniture

Lavkush Furniture is a Django-based furniture catalogue and e-commerce application for Nandurbar, Maharashtra. This release focuses on a complete customer journey, clean product discovery, safer state-changing actions, indexable public pages, and a more polished responsive UI.

## What is included in this release

### Shopping experience
- Searchable, paginated furniture catalogue with category, price, material and sort filters.
- SEO-friendly product URLs: `/gallery/product/<slug>/`.
- Featured products and category navigation are database-driven.
- Guest cart stored in the browser session, with automatic merge after sign-in.
- Account wishlist with a real Clear Wishlist action.
- Checkout page captures a delivery snapshot on the order.
- Order history, order detail, cancellation and 7-day delivered-order return request flow.
- Inventory quantity is checked and decremented under database row locks when payment is confirmed.
- Product ratings now support title and written review text with moderation fields.
- Payment receipts can be viewed and downloaded as PDF.

### Payment reliability
- Razorpay checkout is created server-side only after the cart and delivery details are validated.
- Payment callbacks verify Razorpay signatures on the server.
- Payment finalization locks the payment record to avoid duplicate processing.
- Razorpay webhook endpoint validates the `X-Razorpay-Signature` HMAC and reconciles captured/failed/refunded events.
- If a payment is captured but stock becomes unavailable, the application attempts an automatic Razorpay refund and cancels the order.

### SEO and discoverability
Public pages use self-referencing canonical URLs, dynamic page titles/descriptions, product `Product` structured data, a product sitemap, and a robots policy that keeps private application areas out of indexing. Google does not index a local project automatically; the deployed site still needs to be publicly reachable and submitted/verified in Google Search Console.

### UI/UX
- New responsive visual system with furniture-focused typography, spacing and cards.
- Mobile-first navigation and search.
- Accessible skip link, descriptive image alt text, clearer button labels and reduced-motion support.
- Light/dark theme toggle stored locally.
- Better empty states, stock visibility, order status chips, review presentation and checkout hierarchy.
- Optimized WebP copies of the primary hero/catalog assets plus local favicon/placeholder assets.
- PWA manifest included for a cleaner browser install/share experience.

### Operations and deployment
- SQLite fallback for development; PostgreSQL-ready production configuration.
- `.env.example` documents all required production values.
- Dockerfile, Render blueprint, Procfile and GitHub Actions CI included.
- Seed command for realistic local/demo categories and products: `python manage.py seed_catalog`.
- Bulk CSV/XLSX product import validates file size, image type, image size and safe host/IP rules before saving.
- State-changing operations such as delete/refund/cart/wishlist/cancel actions are POST-only.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
python manage.py migrate
python manage.py seed_catalog
python manage.py createsuperuser
python manage.py runserver
```

For local development, leave `DATABASE_URL` empty and Django will use SQLite. Cloudinary is optional locally; uploaded media will use local file storage until Cloudinary credentials are provided.

## Production environment

Set `DEBUG=False`, a strong `SECRET_KEY`, `SITE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, PostgreSQL `DATABASE_URL`, Cloudinary credentials, Razorpay credentials + webhook secret, real SMTP credentials, and `BULK_IMAGE_ALLOWED_HOSTS`.

Run:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Register the Razorpay webhook URL as:

`https://YOUR-DOMAIN/order/webhook/razorpay/`

Use the same webhook secret in `RAZORPAY_WEBHOOK_SECRET`.

## Google / browser discoverability

1. Deploy the site on a real HTTPS domain.
2. Confirm `/robots.txt` and `/sitemap.xml` are publicly reachable.
3. Add and verify the site in Google Search Console.
4. Submit `/sitemap.xml` and request indexing for the homepage and important product/category pages.
5. Keep product titles, descriptions, prices, availability, images and review content accurate in the database.

Search engines can discover the site from public links and the sitemap, but no code change can guarantee a ranking or instant indexing.

## Store configuration notes

`GST_RATE` and `SHIPPING_FLAT_RATE` are environment-driven so the business can choose the applicable values. This release does not guess a legal GST rate; set the value appropriate to the business and tax configuration.

## Testing

The repository now includes functional tests for registration/profile persistence, slug/SKU creation, catalogue search, ratings, guest/authenticated carts, wishlist clearing, order creation, and POST-only destructive actions. Run:

```bash
python manage.py test
```

## Release packaging

The source-release ZIP intentionally excludes `.git`, `.env`, Python bytecode, logs and local SQLite/media data. Use `.env.example` as the deployment template.
