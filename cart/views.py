from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from gallery.models import ImageWithCaption
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem
import razorpay
from django.conf import settings
from django.shortcuts import render
from .models import Cart
from .models import Payment
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Table, TableStyle

@login_required
def payment_success(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        payment_id = request.POST.get("payment_id")
        amount = request.POST.get("amount")

        payment = Payment.objects.create(
            user=request.user,
            order_id=order_id,
            payment_id=payment_id,
            amount=amount,
            status="Success",
        )

        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        # ✅ Create Order
        order = Order.objects.create(user=request.user, payment=payment)

        # ✅ Save items permanently
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=item.product.caption,
                price=item.product.price,
                quantity=item.quantity,
            )

        # ✅ Clear cart
        cart_items.delete()

        return redirect("cart:payment_receipt", payment.id)


@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, "payment_receipt.html", {"payment": payment})


@login_required
def download_receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
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


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return render(
        request, "view_cart.html", {"items": cart_items, "total_price": total_price}
    )


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(ImageWithCaption, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart:view_cart')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart:view_cart')

@login_required
def update_quantity(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            item.quantity = quantity
            item.save()
        else:
            item.delete()
    return redirect('cart:view_cart')


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

    payment = client.order.create(
        {"amount": amount_in_paise, "currency": "INR", "payment_capture": "1"}
    )

    return render(
        request,
        "payment.html",
        {
            "payment": payment,
            "total_amount": total_amount,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        },
    )
