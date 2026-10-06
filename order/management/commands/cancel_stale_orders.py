from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from order.models import Order


class Command(BaseCommand):
    help = "Cancel orders still waiting for payment after N hours (default 24). Run daily via cron."

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options['hours'])
        stale = Order.objects.filter(order_status='payment_pending', created_at__lt=cutoff).exclude(payment__status='paid')
        count = 0
        for order in stale.select_related('payment'):
            order.order_status = 'cancelled'
            order.cancellation_reason = 'Payment was not completed in time.'
            order.save(update_fields=['order_status', 'cancellation_reason', 'updated_at'])
            if order.payment and order.payment.status == 'pending':
                order.payment.status = 'failed'
                order.payment.save(update_fields=['status'])
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Cancelled {count} stale unpaid order(s).'))
