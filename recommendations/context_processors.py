from .engine import RecommendationEngine


def get_recommendations(request):
    """Inject recommendation data into template context."""
    if request.user.is_authenticated:
        return {
            'has_recommendations': True,
        }
    return {
        'has_recommendations': False,
    }
