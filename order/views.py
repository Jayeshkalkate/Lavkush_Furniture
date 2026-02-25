from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.db.models import Sum
from django.utils import timezone
import razorpay

from cart.models import Cart, CartItem
from .models import Payment, Order, OrderItem

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


@login_required
def admin_finance_dashboard(request):

    if not request.user.is_staff:
        return redirect("home")

    today = timezone.now().date()

    total = (
        Payment.objects.filter(status="paid").aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    daily = (
        Payment.objects.filter(status="paid", created_at__date=today).aggregate(
            Sum("amount")
        )["amount__sum"]
        or 0
    )

    monthly = (
        Payment.objects.filter(
            status="paid",
            created_at__year=today.year,
            created_at__month=today.month,
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    failed = Payment.objects.filter(status="failed").count()

    refunded = (
        Payment.objects.filter(status="refunded").aggregate(Sum("refund_amount"))[
            "refund_amount__sum"
        ]
        or 0
    )

    context = {
        "total": total,
        "daily": daily,
        "monthly": monthly,
        "failed": failed,
        "refunded": refunded,
    }

    return render(request, "admin/finance_dashboard.html", context)


@login_required
def refund_payment(request, payment_id):

    if not request.user.is_staff:
        return redirect("home")

    payment = get_object_or_404(Payment, id=payment_id)

    # ✅ Only allow refund if payment is paid
    if payment.status != "paid":
        return redirect("admin_finance_dashboard")

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        client.payment.refund(payment.payment_id)

        payment.status = "refunded"
        payment.refund_amount = payment.amount
        payment.save()

    except Exception as e:
        print("Refund error:", e)

    return redirect("admin_finance_dashboard")


@login_required
def create_payment(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    total_amount = sum(item.product.price * item.quantity for item in cart_items)

    if total_amount == 0:
        return redirect("cart:view_cart")

    amount_in_paise = int(total_amount * 100)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create(
        {
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": "1",
        }
    )

    # ✅ Save payment as pending
    payment = Payment.objects.create(
        user=request.user,
        order_id=razorpay_order["id"],
        amount=total_amount,
        status="pending",
    )

    return render(
        request,
        "payment.html",
        {
            "payment": razorpay_order,
            "total_amount": total_amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        },
    )


@login_required
def payment_success(request):
    if request.method == "POST":

        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )

            # ✅ Get existing payment
            payment = Payment.objects.get(order_id=razorpay_order_id)

            payment.payment_id = razorpay_payment_id
            payment.signature = razorpay_signature
            payment.status = "paid"
            payment.save()

            # ✅ Create Order
            cart = Cart.objects.get(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)

            order, created = Order.objects.get_or_create(
                payment=payment,
                defaults={
                    "user": request.user,
                    "total_amount": cart.total_amount,
                },
            )

            if created:
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product_name=item.product.caption,
                        price=item.product.price,
                        quantity=item.quantity,
                        )
                    cart_items.delete()

            return redirect("order:payment_receipt", payment.id)

        except:
            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.status = "failed"
            payment.save()

            return redirect("cart:view_cart")


@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, "payment_receipt.html", {"payment": payment})


@login_required
def download_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    order = Order.objects.get(payment=payment)
    order_items = OrderItem.objects.filter(order=order)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Receipt_{payment.payment_id}.pdf"'
    )

    doc = SimpleDocTemplate(response)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Lavkush Furniture</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"Customer: {payment.user.username}", styles["Normal"]))
    elements.append(Paragraph(f"Order ID: {payment.order_id}", styles["Normal"]))
    elements.append(Paragraph(f"Payment ID: {payment.payment_id}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    data = [["Product", "Qty", "Price", "Total"]]

    for item in order_items:
        total = item.price * item.quantity
        data.append(
            [
                item.product_name,
                str(item.quantity),
                f"₹{item.price}",
                f"₹{total}",
            ]
        )

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(f"Total Paid: ₹{payment.amount}", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Thank you for shopping with us!", styles["Normal"]))

    doc.build(elements)
    return response
