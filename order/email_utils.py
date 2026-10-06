import logging
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

def send_order_event_email(order, event, extra=''):
    if not order.email:
        return
    labels = {
        'confirmed': ('Order confirmed', 'Your order is confirmed and is now being prepared.'),
        'shipped': ('Your order has shipped', 'Your order has been shipped. Tracking details are now available on your order page.'),
        'delivered': ('Your order was delivered', 'Your order is marked as delivered. Thank you for shopping with Lavkush Furniture.'),
        'cancelled': ('Order cancelled', 'Your order has been cancelled.'),
        'refunded': ('Payment refunded', 'Your payment refund has been initiated or completed by the payment provider.'),
        'return_pending': ('Return request received', 'We received your return request and the Lavkush Furniture team will review it.'),
        'returned': ('Return completed', 'Your return has been marked completed.'),
    }
    subject, intro = labels.get(event, ('Order update', 'There is an update to your Lavkush Furniture order.'))
    body = f"Hello {order.first_name},\n\nOrder: {order.invoice_number}\nStatus: {order.get_order_status_display()}\n\n{intro}\n{extra}\n\nLavkush Furniture\n{settings.DEFAULT_FROM_EMAIL}"
    try:
        EmailMessage(f'{subject} — {order.invoice_number}', body, settings.DEFAULT_FROM_EMAIL, [order.email]).send(fail_silently=False)
    except Exception:
        logger.exception('Order event email failed for %s', order.invoice_number)
