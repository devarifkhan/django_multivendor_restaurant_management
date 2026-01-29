from django.contrib import admin
from .models import Review, UserActivity


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'fooditem', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__email', 'fooditem__food_title', 'review_text')
    readonly_fields = ('created_at', 'updated_at')


class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'fooditem', 'vendor', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__email', 'search_query')
    readonly_fields = ('created_at',)


admin.site.register(Review, ReviewAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
