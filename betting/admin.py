from django.contrib import admin

from .models import Prediction, PredictionLeaderboard


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ("user", "match", "prediction", "odds", "is_correct", "created_at")
    list_filter = ("is_correct", "match__tournament")
    search_fields = ("user__username", "match__home_team__name", "match__away_team__name")
    autocomplete_fields = ("user", "match")


@admin.register(PredictionLeaderboard)
class PredictionLeaderboardAdmin(admin.ModelAdmin):
    list_display = ("user", "points", "total_predictions", "correct_predictions", "success_rate")
    list_filter = ("user",)
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
