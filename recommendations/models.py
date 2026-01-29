from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from menu.models import FoodItem
from vendor.models import Vendor
from orders.models import Order


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='reviews')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'fooditem', 'order')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.fooditem.food_title} ({self.rating}/5)'


class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ('view', 'Viewed'),
        ('cart', 'Added to Cart'),
        ('order', 'Ordered'),
        ('search', 'Searched'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    fooditem = models.ForeignKey(FoodItem, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    activity_type = models.CharField(max_length=10, choices=ACTIVITY_TYPES)
    search_query = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User activities'

    def __str__(self):
        return f'{self.user.email} - {self.activity_type}'
