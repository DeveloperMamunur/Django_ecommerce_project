from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.utils import timezone

def generate_invoice(order):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 50, f"Invoice: #{order.order_number}")

    # Date
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 70, f"Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}")

    # Payment Status
    payment_status = "Paid" if order.due_amount <= 0 else "Pending"
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, height - 70, f"Payment Status: {payment_status}")

    # Customer Info
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, height - 100, f"Customer: {order.customer.get_full_name()}")
    pdf.drawString(50, height - 115, f"Email: {order.customer.email}")
    if order.shipping_address:
        pdf.drawString(50, height - 130, f"Phone: {order.shipping_address.phone}")
        pdf.drawString(50, height - 145, f"Address: {order.shipping_address.address}, {order.shipping_address.city}, {order.shipping_address.country}")

    # Table header
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, height - 180, "Item")
    pdf.drawString(300, height - 180, "Qty")
    pdf.drawString(350, height - 180, "Price")
    pdf.drawString(450, height - 180, "Total")

    # Table rows
    pdf.setFont("Helvetica", 10)
    y = height - 200
    for item in order.order_details.all():
        pdf.drawString(50, y, item.product.name)
        pdf.drawString(300, y, str(item.quantity))
        pdf.drawString(350, y, f"${item.unit_price:.2f}")
        pdf.drawString(450, y, f"${item.total_price:.2f}")
        y -= 20

    # Subtotal, Shipping, Total
    pdf.drawString(350, y - 20, "Subtotal:")
    pdf.drawString(450, y - 20, f"${order.order_amount:.2f}")
    pdf.drawString(350, y - 40, "Shipping:")
    pdf.drawString(450, y - 40, f"${order.shipping_charge:.2f}")
    pdf.drawString(350, y - 60, "Discount:")
    pdf.drawString(450, y - 60, f"${order.discount + order.coupon_discount:.2f}")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, y - 80, "Total Paid:")
    pdf.drawString(450, y - 80, f"${order.paid_amount:.2f}")
    pdf.drawString(350, y - 100, "Due Amount:")
    pdf.drawString(450, y - 100, f"${order.due_amount:.2f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer
