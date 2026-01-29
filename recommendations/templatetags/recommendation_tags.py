from django import template
from recommendations.engine import RecommendationEngine

register = template.Library()


@register.inclusion_tag('recommendations/partials/star_rating.html')
def star_rating(food_id):
    """Render star rating for a food item."""
    rating_info = RecommendationEngine.get_food_item_rating(food_id)
    return {'rating_info': rating_info}


@register.inclusion_tag('recommendations/partials/vendor_rating.html')
def vendor_rating(vendor_id):
    """Render star rating for a vendor."""
    rating_info = RecommendationEngine.get_vendor_rating(vendor_id)
    return {'rating_info': rating_info}


@register.inclusion_tag('recommendations/partials/recommendation_section.html', takes_context=True)
def recommendation_section(context, section_type, title='Recommended for You'):
    """Render a recommendation section."""
    request = context['request']
    user = request.user
    items = []

    if section_type == 'order_again' and user.is_authenticated:
        items = RecommendationEngine.get_order_again(user, limit=6)
    elif section_type == 'trending':
        items = RecommendationEngine.get_trending_items(limit=6)
    elif section_type == 'top_rated':
        items = RecommendationEngine.get_top_rated_items(limit=6)
    elif section_type == 'for_you' and user.is_authenticated:
        items = RecommendationEngine.get_customers_also_ordered(user, limit=6)
    elif section_type == 'category_based' and user.is_authenticated:
        items = RecommendationEngine.get_category_recommendations(user, limit=6)

    return {
        'items': items,
        'title': title,
        'section_type': section_type,
    }


@register.inclusion_tag('recommendations/partials/vendor_recommendation_section.html', takes_context=True)
def vendor_recommendations(context, title='Recommended Restaurants'):
    """Render vendor recommendation section."""
    request = context['request']
    user = request.user
    vendors = []

    if user.is_authenticated:
        vendors = RecommendationEngine.get_vendor_recommendations(user, limit=6)

    return {
        'recommended_vendors': vendors,
        'title': title,
    }
