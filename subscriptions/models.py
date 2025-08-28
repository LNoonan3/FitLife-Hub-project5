from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    INTERVAL_CHOICES = [('monthly', 'Monthly'), ('yearly', 'Yearly')]
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    interval = models.CharField(max_length=10, choices=INTERVAL_CHOICES)
    is_active = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    stripe_sub_id = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} → {self.plan.name}"
