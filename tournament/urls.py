from django.urls import path

from . import views


urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('teams/', views.teams_list, name='teams'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    path('matches/', views.matches_list, name='matches'),
    path('matches/<int:pk>/', views.match_detail, name='match_detail'),
    path('standings/', views.standings_view, name='standings'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('bracket/', views.bracket_view, name='bracket'),

    path('inscription/', views.register_team, name='register_team'),
    path('inscription/merci/', views.register_team_success, name='register_team_success'),

    # API (AJAX)
    path('api/live-scores/', views.live_scores_api, name='live_scores_api'),
    path('api/matches/<int:pk>/goals/', views.match_goals_api, name='match_goals_api'),

    # Admin panel (custom)
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/tournament/', views.admin_tournament_setup, name='admin_tournament_setup'),

    path('admin-panel/teams/', views.admin_teams, name='admin_teams'),
    path('admin-panel/teams/add/', views.admin_add_team, name='admin_add_team'),
    path('admin-panel/teams/<int:pk>/edit/', views.admin_edit_team, name='admin_edit_team'),
    path('admin-panel/teams/<int:pk>/delete/', views.admin_delete_team, name='admin_delete_team'),
    path('admin-panel/teams/<int:team_pk>/players/add/', views.admin_add_player, name='admin_add_player'),
    path('admin-panel/players/<int:pk>/delete/', views.admin_delete_player, name='admin_delete_player'),

    path('admin-panel/matches/', views.admin_matches, name='admin_matches'),
    path('admin-panel/matches/add/', views.admin_add_match, name='admin_add_match'),
    path('admin-panel/matches/<int:pk>/edit/', views.admin_edit_match, name='admin_edit_match'),
    path('admin-panel/matches/<int:pk>/score/', views.admin_update_score, name='admin_update_score'),
    path('admin-panel/matches/<int:match_pk>/goals/add/', views.admin_add_goal, name='admin_add_goal'),
    path('admin-panel/matches/generate/', views.admin_generate_matches, name='admin_generate_matches'),

    path('admin-panel/knockout/generate/', views.admin_generate_knockout, name='admin_generate_knockout'),
    path('admin-panel/knockout/<int:pk>/score/', views.admin_knockout_score, name='admin_knockout_score'),

    # Ticket management
    path('admin-panel/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin-panel/matches/<int:match_pk>/tickets/config/', views.admin_ticket_config, name='admin_ticket_config'),
    path('admin-panel/tickets/<int:config_pk>/generate/', views.admin_generate_tickets, name='admin_generate_tickets'),
    path('admin-panel/tickets/<int:config_pk>/download/', views.admin_download_tickets, name='admin_download_tickets'),
    path('admin-panel/tickets/<int:config_pk>/preview/', views.admin_preview_ticket, name='admin_preview_ticket'),
    path('admin-panel/tickets/<int:config_pk>/delete/', views.admin_delete_tickets, name='admin_delete_tickets'),

    # Ticket Designer - Cool & Unique
    path('admin-panel/ticket-designer/', views.admin_ticket_designer, name='admin_ticket_designer'),
    path('admin-panel/matches/<int:match_pk>/tickets/cool/preview/', views.admin_preview_cool_ticket, name='admin_preview_cool_ticket'),
    path('admin-panel/matches/<int:match_pk>/tickets/cool/generate/', views.admin_generate_cool_tickets, name='admin_generate_cool_tickets'),
    path('admin-panel/tickets/cool/<int:ticket_pk>/download/', views.admin_download_individual_cool_ticket, name='admin_download_individual_cool_ticket'),
]

