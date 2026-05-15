from django.contrib import admin

from .models import Tournament, Group, Team, Player, Match, Goal, Standing, KnockoutMatch, TeamRegistration


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "edition", "start_date", "end_date", "location", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "edition", "location")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("tournament", "name")
    list_filter = ("tournament", "name")
    search_fields = ("tournament__name",)


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "tournament", "group", "created_at")
    list_filter = ("tournament", "group")
    search_fields = ("name", "tournament__name")
    autocomplete_fields = ("tournament", "group")
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "team", "position", "age", "jersey_number", "is_captain")
    list_filter = ("position", "is_captain", "team__tournament")
    search_fields = ("first_name", "last_name", "team__name")
    autocomplete_fields = ("team",)


class GoalInline(admin.TabularInline):
    model = Goal
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("tournament", "phase", "group", "home_team", "away_team", "match_date", "status", "matchday")
    list_filter = ("tournament", "phase", "status", "group")
    search_fields = ("home_team__name", "away_team__name", "tournament__name")
    autocomplete_fields = ("tournament", "group", "home_team", "away_team")
    inlines = [GoalInline]


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("match", "team", "player", "minute", "is_own_goal", "is_penalty", "created_at")
    list_filter = ("is_own_goal", "is_penalty", "team__tournament")
    search_fields = ("player__first_name", "player__last_name", "team__name")
    autocomplete_fields = ("match", "team", "player")


@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("group", "team", "played", "won", "drawn", "lost", "goals_for", "goals_against", "points")
    list_filter = ("group__tournament", "group")
    search_fields = ("team__name",)
    autocomplete_fields = ("group", "team")


@admin.register(KnockoutMatch)
class KnockoutMatchAdmin(admin.ModelAdmin):
    list_display = ("tournament", "round", "match_number", "home_team", "away_team", "match_date", "status", "winner")
    list_filter = ("tournament", "round", "status")
    search_fields = ("home_team__name", "away_team__name", "tournament__name")
    autocomplete_fields = ("tournament", "home_team", "away_team", "winner")


@admin.register(TeamRegistration)
class TeamRegistrationAdmin(admin.ModelAdmin):
    list_display = ("team_name", "captain_name", "phone", "neighborhood", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("team_name", "captain_name", "phone")
    readonly_fields = ("submitted_at", "payment_proof")
