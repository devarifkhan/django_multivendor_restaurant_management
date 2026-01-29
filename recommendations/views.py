from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from menu.models import FoodItem
from orders.models import Order, OrderedFood
from .models import Review, UserActivity
from .forms import ReviewForm
from .engine import RecommendationEngine


@login_required(login_url='login')
def add_review(request, order_number, food_id):
    """Add a review for an ordered food item."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user, is_ordered=True)
    fooditem = get_object_or_404(FoodItem, id=food_id)

    # Verify the user actually ordered this item in this order
    ordered_food = OrderedFood.objects.filter(order=order, fooditem=fooditem, user=request.user).first()
    if not ordered_food:
        messages.error(request, 'You can only review items you have ordered.')
        return redirect('order_detail', order_number=order_number)

    # Check if already reviewed
    existing_review = Review.objects.filter(user=request.user, fooditem=fooditem, order=order).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.fooditem = fooditem
            review.order = order
            review.save()
            messages.success(request, 'Your review has been submitted!')
            return redirect('order_detail', order_number=order_number)
    else:
        form = ReviewForm(instance=existing_review)

    context = {
        'form': form,
        'fooditem': fooditem,
        'order': order,
        'existing_review': existing_review,
    }
    return render(request, 'recommendations/add_review.html', context)


def food_reviews(request, food_id):
    """View all reviews for a food item."""
    fooditem = get_object_or_404(FoodItem, id=food_id)
    reviews = Review.objects.filter(fooditem=fooditem).select_related('user')
    rating_info = RecommendationEngine.get_food_item_rating(food_id)

    context = {
        'fooditem': fooditem,
        'reviews': reviews,
        'rating_info': rating_info,
    }
    return render(request, 'recommendations/food_reviews.html', context)


def vendor_reviews(request, vendor_slug):
    """View all reviews for a vendor."""
    from vendor.models import Vendor
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    reviews = Review.objects.filter(fooditem__vendor=vendor).select_related('user', 'fooditem')
    rating_info = RecommendationEngine.get_vendor_rating(vendor.id)

    context = {
        'vendor': vendor,
        'reviews': reviews,
        'rating_info': rating_info,
    }
    return render(request, 'recommendations/vendor_reviews.html', context)


def frequently_bought_together(request, food_id):
    """AJAX endpoint for frequently bought together items."""
    items = RecommendationEngine.get_frequently_bought_together(food_id, limit=4)
    data = []
    for item in items:
        data.append({
            'id': item.id,
            'title': item.food_title,
            'price': str(item.price),
            'image': item.image.url if item.image else '',
            'vendor': item.vendor.vendor_name,
            'vendor_slug': item.vendor.vendor_slug,
        })
    return JsonResponse({'items': data})


def similar_items(request, food_id):
    """AJAX endpoint for similar items."""
    items = RecommendationEngine.get_similar_items(food_id, limit=4)
    data = []
    for item in items:
        rating = getattr(item, 'avg_rating', 0)
        data.append({
            'id': item.id,
            'title': item.food_title,
            'price': str(item.price),
            'image': item.image.url if item.image else '',
            'vendor': item.vendor.vendor_name,
            'vendor_slug': item.vendor.vendor_slug,
            'avg_rating': round(rating, 1) if rating else 0,
        })
    return JsonResponse({'items': data})


def track_activity(request):
    """AJAX endpoint to track user activity (view, search)."""
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'ignored'})

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == 'POST':
        activity_type = request.POST.get('activity_type')
        food_id = request.POST.get('food_id')
        vendor_id = request.POST.get('vendor_id')
        search_query = request.POST.get('search_query', '')

        activity = UserActivity(user=request.user, activity_type=activity_type)

        if food_id:
            try:
                activity.fooditem_id = int(food_id)
            except (ValueError, TypeError):
                pass
        if vendor_id:
            try:
                activity.vendor_id = int(vendor_id)
            except (ValueError, TypeError):
                pass
        if search_query:
            activity.search_query = search_query[:200]

        activity.save()
        return JsonResponse({'status': 'tracked'})

    return JsonResponse({'status': 'invalid'})
