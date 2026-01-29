from django.urls import path
from . import views

urlpatterns = [
    path('review/<str:order_number>/<int:food_id>/', views.add_review, name='add_review'),
    path('food-reviews/<int:food_id>/', views.food_reviews, name='food_reviews'),
    path('vendor-reviews/<str:vendor_slug>/', views.vendor_reviews, name='vendor_reviews'),
    path('frequently-bought-together/<int:food_id>/', views.frequently_bought_together, name='frequently_bought_together'),
    path('similar-items/<int:food_id>/', views.similar_items, name='similar_items'),
    path('track-activity/', views.track_activity, name='track_activity'),
]
