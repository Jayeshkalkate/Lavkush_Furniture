from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def backfill_order_snapshots(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('account', 'Items')
    Order = apps.get_model('order', 'Order')
    profiles = {p.user_id: p for p in Profile.objects.all()}
    for order in Order.objects.all():
        user = User.objects.filter(pk=order.user_id).first()
        profile = profiles.get(order.user_id)
        order.first_name = (user.first_name if user else '') or (user.username if user else '')
        order.last_name = user.last_name if user else ''
        order.shipping_address = profile.address if profile else ''
        order.city = profile.city if profile else ''
        order.state = 'Maharashtra'
        order.postal_code = '425412'
        order.country = 'India'
        order.phone = profile.phone_number if profile else ''
        order.email = user.email if user else ''
        order.subtotal = order.total_amount or 0
        if not order.order_status:
            order.order_status = 'processing'
        order.save()


class Migration(migrations.Migration):
    dependencies = [
        ('gallery', '0002_catalog_upgrade'),
        ('order', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(model_name='payment', name='gateway_status', field=models.CharField(blank=True, max_length=50)),
        migrations.AddField(model_name='payment', name='webhook_event', field=models.CharField(blank=True, max_length=100)),
        migrations.AddField(model_name='payment', name='gateway_response', field=models.JSONField(blank=True, default=dict)),
        migrations.AddField(model_name='payment', name='paid_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='payment', name='refunded_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AlterField(model_name='order', name='payment', field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order', to='order.payment')),
        migrations.AddField(model_name='order', name='subtotal', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='order', name='shipping_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='order', name='tax_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='order', name='discount_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='order', name='shipping_method', field=models.CharField(default='Standard delivery', max_length=100)),
        migrations.AddField(model_name='order', name='tracking_number', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='order', name='shipping_provider', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='order', name='expected_delivery', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='order', name='shipped_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='order', name='delivered_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='order', name='cancellation_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='order', name='return_requested', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='order', name='return_reason', field=models.TextField(blank=True)),
        migrations.AddField(model_name='order', name='return_status', field=models.CharField(choices=[('none', 'None'), ('requested', 'Requested'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='none', max_length=20)),
        migrations.AddField(model_name='order', name='inventory_deducted', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='order', name='updated_at', field=models.DateTimeField(auto_now=True)),
        migrations.AddField(model_name='order', name='first_name', field=models.CharField(default='', max_length=100)),
        migrations.AddField(model_name='order', name='last_name', field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AddField(model_name='order', name='company', field=models.CharField(blank=True, default='', max_length=160)),
        migrations.AddField(model_name='order', name='shipping_address', field=models.TextField(default='')),
        migrations.AddField(model_name='order', name='address_line2', field=models.CharField(blank=True, default='', max_length=255)),
        migrations.AddField(model_name='order', name='city', field=models.CharField(default='', max_length=120)),
        migrations.AddField(model_name='order', name='state', field=models.CharField(default='', max_length=120)),
        migrations.AddField(model_name='order', name='postal_code', field=models.CharField(default='', max_length=20)),
        migrations.AddField(model_name='order', name='country', field=models.CharField(default='India', max_length=80)),
        migrations.AddField(model_name='order', name='phone', field=models.CharField(default='', max_length=20)),
        migrations.AddField(model_name='order', name='email', field=models.EmailField(default='', max_length=254)),
        migrations.AddField(model_name='order', name='order_notes', field=models.TextField(blank=True)),
        migrations.AlterField(model_name='order', name='order_status', field=models.CharField(choices=[('payment_pending', 'Payment Pending'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('return_pending', 'Return Requested'), ('returned', 'Returned')], db_index=True, default='payment_pending', max_length=30)),
        migrations.AddField(model_name='orderitem', name='product', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_items', to='gallery.imagewithcaption')),
        migrations.AddField(model_name='orderitem', name='sku', field=models.CharField(blank=True, default='', max_length=80)),
        migrations.AddIndex(model_name='order', index=models.Index(fields=['user', '-created_at'], name='order_order_user_id_5a7e9b_idx')),
        migrations.AddIndex(model_name='order', index=models.Index(fields=['order_status', '-created_at'], name='order_order_status_4d7a4b_idx')),
        migrations.RunPython(backfill_order_snapshots, migrations.RunPython.noop),
    ]
