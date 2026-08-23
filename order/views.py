import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
import razorpay

from cart.models import Cart, CartItem
from .models import Payment, Order, OrderItem

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger(__name__)


def get_razorpay_client():
    """Helper to get Razorpay client with keys from settings."""
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


# ===============================
# 💰 ADMIN FINANCE DASHBOARD
# ===============================
@login_required
def admin_finance_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect("homepage")

    today = timezone.now().date()

    # Use efficient aggregations
    totals = Payment.objects.filter(status="paid").aggregate(
        total=Sum("amount"), daily=Sum("amount", filter=models.Q(created_at__date=today)),
        monthly=Sum("amount", filter=models.Q(created_at__year=today.year, created_at__month=today.month))
    )
    total = totals.get("total") or 0
    daily = totals.get("daily") or 0
    monthly = totals.get("monthly") or 0

    failed = Payment.objects.filter(status="failed").count()
    refunded = Payment.objects.filter(status="refunded").aggregate(refund=Sum("refund_amount"))["refund"] or 0

    payments = Payment.objects.select_related("user").order_by("-created_at")[:20]

    context = {
        "total": total,
        "daily": daily,
        "monthly": monthly,
        "failed": failed,
        "refunded": refunded,
        "payments": payments,
    }
    return render(request, "admin_finance_dashboard.html", context)


# ===============================
# 🔁 REFUND PAYMENT
# ===============================
@login_required
def refund_payment(request, payment_id):
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect("homepage")

    payment = get_object_or_404(Payment, id=payment_id)
    if payment.status != "paid":
        messages.warning(request, "Payment is not in 'paid' status.")
        return redirect("admin_finance_dashboard")

    client = get_razorpay_client()
    try:
        client.payment.refund(payment.payment_id)
        payment.status = "refunded"
        payment.refund_amount = payment.amount
        payment.save()
        messages.success(request, f"Refund processed for payment {payment.payment_id}.")
        logger.info(f"Admin {request.user.username} refunded payment {payment.payment_id}")
    except Exception as e:
        logger.error(f"Refund error: {e}")
        messages.error(request, f"Refund failed: {str(e)}")

    return redirect("admin_finance_dashboard")


# ===============================
# 💳 CREATE PAYMENT (CHECKOUT)
# ===============================
@login_required
def create_payment(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    total_amount = sum(item.subtotal for item in cart_items)

    if total_amount <= 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("cart:view_cart")

    amount_in_paise = int(total_amount * 100)
    client = get_razorpay_client()

    try:
        razorpay_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1",
        })
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        messages.error(request, "Payment gateway error. Please try again.")
        return redirect("cart:view_cart")

    payment = Payment.objects.create(
        user=request.user,
        order_id=razorpay_order["id"],
        amount=total_amount,
        status="pending",
    )

    context = {
        "payment": razorpay_order,
        "total_amount": total_amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    }
    return render(request, "payment.html", context)


# ===============================
# ✅ PAYMENT SUCCESS
# ===============================
@login_required
@transaction.atomic
def payment_success(request):
    if request.method != "POST":
        return redirect("cart:view_cart")

    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        messages.error(request, "Invalid payment response.")
        return redirect("cart:view_cart")

    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        Payment.objects.filter(order_id=razorpay_order_id, user=request.user).update(status="failed")
        messages.error(request, "Payment verification failed.")
        return redirect("cart:view_cart")

    payment = get_object_or_404(Payment, order_id=razorpay_order_id, user=request.user)
    payment.payment_id = razorpay_payment_id
    payment.signature = razorpay_signature
    payment.status = "paid"
    payment.save()

    # Create order
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.select_related('product').all()
    order = Order.objects.create(
        user=request.user,
        payment=payment,
        total_amount=payment.amount,
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product_name=item.product.caption,
            price=item.product.price,
            quantity=item.quantity,
        )

    cart_items.delete()  # empty cart
    messages.success(request, "Payment successful! Order placed.")
    return redirect("order:payment_receipt", payment.id)


# ===============================
# 🧾 RECEIPT VIEW
# ===============================
@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, "payment_receipt.html", {"payment": payment})


# ===============================
# 📊 USER FINANCE DASHBOARD
# ===============================
@login_required
def customer_finance_dashboard(request):
    today = timezone.now().date()
    qs = Payment.objects.filter(user=request.user, status="paid")
    total = qs.aggregate(total=Sum("amount"))["total"] or 0
    monthly = qs.filter(created_at__year=today.year, created_at__month=today.month).aggregate(monthly=Sum("amount"))["monthly"] or 0
    failed = Payment.objects.filter(user=request.user, status="failed").count()
    refunded = Payment.objects.filter(user=request.user, status="refunded").aggregate(refund=Sum("refund_amount"))["refund"] or 0

    payments = Payment.objects.filter(user=request.user).select_related("user").order_by("-created_at")[:10]

    context = {
        "total": total,
        "monthly": monthly,
        "failed": failed,
        "refunded": refunded,
        "payments": payments,
    }
    return render(request, "customer_finance_dashboard.html", context)


# ===============================
# 📄 DOWNLOAD RECEIPT PDF
# ===============================
@login_required
def download_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    order = get_object_or_404(Order, payment=payment)
    order_items = order.items.all()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Receipt_{payment.payment_id or payment.id}.pdf"'

    doc = SimpleDocTemplate(response)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    elements.append(Paragraph("<b>Lavkush Furniture</b>", title_style))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Date: {payment.created_at.strftime('%d %b %Y %H:%M')}", styles["Normal"]))
    elements.append(Paragraph(f"Customer: {payment.user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Order ID: {order.invoice_number}", styles["Normal"]))
    elements.append(Paragraph(f"Payment ID: {payment.payment_id}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [["Product", "Qty", "Price", "Total"]]
    for item in order_items:
        total = item.price * item.quantity
        data.append([item.product_name, str(item.quantity), f"₹{item.price}", f"₹{total}"])

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph(f"Total Paid: ₹{payment.amount}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Thank you for shopping with us!", styles["Normal"]))

    doc.build(elements)
    return response
