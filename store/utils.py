from django.core.mail import send_mail
from django.conf import settings


def send_order_confirmation_email(user, order):
    subject = "Your FitLife Hub Order Confirmation"
    message = (
        f"Hi {user.first_name or user.username},\n\n"
        f"Thank you for your order #{order.id}!\n"
        f"Order total: €{order.total_cents / 100:.2f}\n"
        "We'll notify you when your order ships.\n\n"
        "FitLife Hub Team"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
