from django.db import migrations, models


def seed_demo_coupon(apps, schema_editor):
    Coupon = apps.get_model('order', 'Coupon')
    Coupon.objects.get_or_create(code='WELCOME10', defaults={
        'discount_type': 'percent', 'value': 10, 'active': True,
        'minimum_order_value': 5000, 'usage_limit': 100,
    })


class Migration(migrations.Migration):
    dependencies = [('order', '0002_order_checkout_upgrade')]
    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(db_index=True, max_length=40, unique=True)),
                ('discount_type', models.CharField(choices=[('percent', 'Percentage'), ('fixed', 'Fixed amount')], default='percent', max_length=10)),
                ('value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('active', models.BooleanField(db_index=True, default=True)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_until', models.DateTimeField(blank=True, null=True)),
                ('usage_limit', models.PositiveIntegerField(blank=True, null=True)),
                ('uses', models.PositiveIntegerField(default=0)),
                ('minimum_order_value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.AddField(model_name='order', name='coupon_code', field=models.CharField(blank=True, default='', max_length=40)),
        migrations.RunPython(seed_demo_coupon, migrations.RunPython.noop),
    ]
