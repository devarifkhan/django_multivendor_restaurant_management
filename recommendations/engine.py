from django.db.models import Count, Avg, Q, F
from django.db.models.functions import Coalesce
from collections import Counter

from menu.models import FoodItem, Category
from orders.models import OrderedFood, Order
from vendor.models import Vendor
from .models import Review, UserActivity


class RecommendationEngine:
    """Amazon-style recommendation engine for food items and vendors."""

    @staticmethod
    def get_order_again(user, limit=10):
        """Items the user has ordered before - 'Order Again'"""
        ordered_items = (
            OrderedFood.objects
            .filter(user=user, order__is_ordered=True)
            .values('fooditem')
            .annotate(
                times_ordered=Count('id'),
                last_ordered=models.Max('created_at')
            )
            .order_by('-times_ordered')[:limit]
        )
        food_ids = [item['fooditem'] for item in ordered_items]
        return FoodItem.objects.filter(
            id__in=food_ids,
            is_available=True
        ).select_related('vendor', 'category')

    @staticmethod
    def get_frequently_bought_together(fooditem_id, limit=6):
        """Items frequently ordered together with this item."""
        # Find orders containing this item
        order_ids = (
            OrderedFood.objects
            .filter(fooditem_id=fooditem_id, order__is_ordered=True)
            .values_list('order_id', flat=True)
        )
        # Find other items in those same orders
        paired_items = (
            OrderedFood.objects
            .filter(order_id__in=order_ids, order__is_ordered=True)
            .exclude(fooditem_id=fooditem_id)
            .values('fooditem')
            .annotate(pair_count=Count('id'))
            .order_by('-pair_count')[:limit]
        )
        food_ids = [item['fooditem'] for item in paired_items]
        return FoodItem.objects.filter(
            id__in=food_ids,
            is_available=True
        ).select_related('vendor', 'category')

    @staticmethod
    def get_customers_also_ordered(user, limit=10):
        """'Customers who ordered your items also ordered' - collaborative filtering."""
        # Get items this user has ordered
        user_food_ids = (
            OrderedFood.objects
            .filter(user=user, order__is_ordered=True)
            .values_list('fooditem_id', flat=True)
            .distinct()
        )
        if not user_food_ids:
            return FoodItem.objects.none()

        # Find other users who ordered the same items
        similar_users = (
            OrderedFood.objects
            .filter(fooditem_id__in=user_food_ids, order__is_ordered=True)
            .exclude(user=user)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Find items those similar users ordered that this user hasn't
        recommended = (
            OrderedFood.objects
            .filter(user_id__in=similar_users, order__is_ordered=True)
            .exclude(fooditem_id__in=user_food_ids)
            .values('fooditem')
            .annotate(score=Count('id'))
            .order_by('-score')[:limit]
        )
        food_ids = [item['fooditem'] for item in recommended]
        return FoodItem.objects.filter(
            id__in=food_ids,
            is_available=True
        ).select_related('vendor', 'category')

    @staticmethod
    def get_trending_items(limit=10):
        """Trending / Most Popular items based on recent orders."""
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now() - timedelta(days=30)
        trending = (
            OrderedFood.objects
            .filter(order__is_ordered=True, created_at__gte=thirty_days_ago)
            .values('fooditem')
            .annotate(order_count=Count('id'))
            .order_by('-order_count')[:limit]
        )
        food_ids = [item['fooditem'] for item in trending]
        return FoodItem.objects.filter(
            id__in=food_ids,
            is_available=True
        ).select_related('vendor', 'category')

    @staticmethod
    def get_top_rated_items(limit=10):
        """Top rated food items based on reviews."""
        top_rated = (
            Review.objects
            .values('fooditem')
            .annotate(
                avg_rating=Avg('rating'),
                review_count=Count('id')
            )
            .filter(review_count__gte=1)
            .order_by('-avg_rating', '-review_count')[:limit]
        )
        food_ids = [item['fooditem'] for item in top_rated]
        items = FoodItem.objects.filter(
            id__in=food_ids,
            is_available=True
        ).select_related('vendor', 'category')

        # Annotate with avg rating
        return items.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

    @staticmethod
    def get_category_recommendations(user, limit=10):
        """Recommend items from categories the user frequently orders from."""
        # Find user's most ordered categories
        user_categories = (
            OrderedFood.objects
            .filter(user=user, order__is_ordered=True)
            .values('fooditem__category')
            .annotate(cat_count=Count('id'))
            .order_by('-cat_count')[:3]
        )
        category_ids = [c['fooditem__category'] for c in user_categories]

        if not category_ids:
            return FoodItem.objects.none()

        # Get user's already ordered items to exclude
        ordered_ids = (
            OrderedFood.objects
            .filter(user=user, order__is_ordered=True)
            .values_list('fooditem_id', flat=True)
            .distinct()
        )

        return (
            FoodItem.objects
            .filter(category_id__in=category_ids, is_available=True)
            .exclude(id__in=ordered_ids)
            .select_related('vendor', 'category')
            .annotate(
                avg_rating=Coalesce(Avg('reviews__rating'), 0.0),
            )
            .order_by('-avg_rating')[:limit]
        )

    @staticmethod
    def get_vendor_recommendations(user, limit=6):
        """Recommend vendors based on user's ordering patterns."""
        # Vendors user has ordered from
        ordered_vendor_ids = (
            OrderedFood.objects
            .filter(user=user, order__is_ordered=True)
            .values_list('fooditem__vendor_id', flat=True)
            .distinct()
        )

        if not ordered_vendor_ids:
            # Return top vendors by order count
            top_vendors = (
                OrderedFood.objects
                .filter(order__is_ordered=True)
                .values('fooditem__vendor')
                .annotate(order_count=Count('id'))
                .order_by('-order_count')[:limit]
            )
            vendor_ids = [v['fooditem__vendor'] for v in top_vendors]
            return Vendor.objects.filter(
                id__in=vendor_ids,
                is_approved=True,
                user__is_active=True
            )

        # Find users with similar vendor preferences
        similar_users = (
            OrderedFood.objects
            .filter(
                fooditem__vendor_id__in=ordered_vendor_ids,
                order__is_ordered=True
            )
            .exclude(user=user)
            .values_list('user_id', flat=True)
            .distinct()
        )

        # Get vendors those users ordered from that this user hasn't
        recommended_vendors = (
            OrderedFood.objects
            .filter(user_id__in=similar_users, order__is_ordered=True)
            .exclude(fooditem__vendor_id__in=ordered_vendor_ids)
            .values('fooditem__vendor')
            .annotate(score=Count('id'))
            .order_by('-score')[:limit]
        )
        vendor_ids = [v['fooditem__vendor'] for v in recommended_vendors]
        return Vendor.objects.filter(
            id__in=vendor_ids,
            is_approved=True,
            user__is_active=True
        )

    @staticmethod
    def get_similar_items(fooditem_id, limit=6):
        """Items similar to this one (same category, same vendor)."""
        try:
            item = FoodItem.objects.get(id=fooditem_id)
        except FoodItem.DoesNotExist:
            return FoodItem.objects.none()

        return (
            FoodItem.objects
            .filter(
                Q(category=item.category) | Q(vendor=item.vendor),
                is_available=True
            )
            .exclude(id=fooditem_id)
            .select_related('vendor', 'category')
            .annotate(
                avg_rating=Coalesce(Avg('reviews__rating'), 0.0),
            )
            .order_by('-avg_rating')
            .distinct()[:limit]
        )

    @staticmethod
    def get_personalized_homepage(user, limit=12):
        """Full personalized recommendations for homepage."""
        recommendations = {
            'order_again': [],
            'trending': [],
            'top_rated': [],
            'for_you': [],
            'recommended_vendors': [],
        }

        if user.is_authenticated:
            recommendations['order_again'] = RecommendationEngine.get_order_again(user, limit=6)
            recommendations['for_you'] = RecommendationEngine.get_customers_also_ordered(user, limit=6)
            recommendations['recommended_vendors'] = RecommendationEngine.get_vendor_recommendations(user, limit=6)

        recommendations['trending'] = RecommendationEngine.get_trending_items(limit=6)
        recommendations['top_rated'] = RecommendationEngine.get_top_rated_items(limit=6)

        return recommendations

    @staticmethod
    def get_food_item_rating(fooditem_id):
        """Get average rating and review count for a food item."""
        result = Review.objects.filter(fooditem_id=fooditem_id).aggregate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
        )
        return {
            'avg_rating': round(result['avg_rating'] or 0, 1),
            'review_count': result['review_count'] or 0,
        }

    @staticmethod
    def get_vendor_rating(vendor_id):
        """Get average rating and review count for a vendor."""
        result = Review.objects.filter(fooditem__vendor_id=vendor_id).aggregate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
        )
        return {
            'avg_rating': round(result['avg_rating'] or 0, 1),
            'review_count': result['review_count'] or 0,
        }


# Need to import models for the Max aggregation
from django.db import models
