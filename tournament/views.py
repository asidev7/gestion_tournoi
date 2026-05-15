from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, FileResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Tournament, Group, Team, Player, Match, Goal, Standing, KnockoutMatch
from .forms import (TeamForm, PlayerForm, MatchForm, GoalForm,
                    ScoreUpdateForm, KnockoutMatchForm, TournamentForm, TeamRegistrationForm, TicketConfigForm)
from .models import Tournament, Group, Team, Player, Match, Goal, Standing, KnockoutMatch, TeamRegistration, TicketConfig, Ticket
from .pdf_generator import generate_tickets_pdf, generate_ticket_preview
from .ticket_designer import (
    generate_cool_ticket_pdf,
    generate_bulk_cool_tickets,
    generate_ticket_from_model,
    generate_unique_ticket_number
)
import json
from datetime import timedelta


def is_admin(user):
    return user.is_staff or user.is_superuser


def get_active_tournament():
    today = timezone.localdate()
    active = Tournament.objects.filter(is_active=True)

    ongoing = active.filter(
        start_date__isnull=False,
        end_date__isnull=False,
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('start_date').first()
    if ongoing:
        return ongoing

    upcoming = active.filter(
        start_date__isnull=False,
        start_date__gte=today,
    ).order_by('start_date').first()
    if upcoming:
        return upcoming

    return active.order_by('-start_date', '-id').first()


def _sync_match_statuses(tournament=None):
    now = timezone.now()

    scheduled_matches = Match.objects.filter(
        status='SCHEDULED',
        match_date__isnull=False,
        match_date__lte=now,
    )
    if tournament:
        scheduled_matches = scheduled_matches.filter(tournament=tournament)

    for match in scheduled_matches:
        match.status = 'LIVE'
        if not match.live_started_at:
            match.live_started_at = match.match_date or now
        match.save(update_fields=['status', 'live_started_at'])

    live_threshold = now - timedelta(minutes=105)
    live_matches = Match.objects.filter(status='LIVE').filter(
        Q(live_started_at__lte=live_threshold) |
        Q(live_started_at__isnull=True, match_date__isnull=False, match_date__lte=live_threshold)
    )
    if tournament:
        live_matches = live_matches.filter(tournament=tournament)

    for match in live_matches:
        if not match.live_started_at and match.match_date:
            match.live_started_at = match.match_date
        match.status = 'FINISHED'
        update_fields = ['status']
        if match.live_started_at:
            update_fields.append('live_started_at')
        match.save(update_fields=update_fields)
        _update_standings(match)
        _check_predictions(match)


# ─── Public Views ───────────────────────────────────────────

def home(request):
    tournament = get_active_tournament()
    _sync_match_statuses(tournament)
    matches = (
        Match.objects.filter(tournament=tournament)
        .select_related('home_team', 'away_team', 'group')
        if tournament else Match.objects.none()
    )
    next_matches = matches.filter(status='SCHEDULED').order_by('match_date')[:5]
    live_matches = matches.filter(status='LIVE').order_by('match_date')
    recent_results = matches.filter(status='FINISHED').order_by('-match_date')[:5]
    top_scorers = (
        Player.objects.filter(team__tournament=tournament)
        .annotate(goal_count=Count('goals', filter=Q(goals__match__tournament=tournament)))
        .filter(goal_count__gt=0)
        .order_by('-goal_count')[:5]
        if tournament
        else Player.objects.none()
    )

    context = {
        'tournament': tournament,
        'hero_match': live_matches.first() if tournament else None,
        'next_matches': next_matches,
        'live_matches': live_matches,
        'recent_results': recent_results,
        'top_scorers': top_scorers,
        'stats': {
            'teams': tournament.teams.count() if tournament else 0,
            'matches': matches.count() if tournament else 0,
            'live': live_matches.count() if tournament else 0,
            'completed': recent_results.count() if tournament else 0,
        },
    }
    return render(request, 'home.html', context)


def teams_list(request):
    tournament = get_active_tournament()
    groups = Group.objects.filter(tournament=tournament).prefetch_related('teams') if tournament else []
    teams_no_group = Team.objects.filter(tournament=tournament, group__isnull=True) if tournament else []
    return render(request, 'tournament/teams.html', {
        'tournament': tournament,
        'groups': groups,
        'teams_no_group': teams_no_group,
    })


def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    players = team.players.all()
    matches = Match.objects.filter(
        Q(home_team=team) | Q(away_team=team)
    ).order_by('match_date')
    standings = Standing.objects.filter(team=team).first()
    goals = Goal.objects.filter(team=team).select_related('player', 'match')
    return render(request, 'tournament/team_detail.html', {
        'team': team,
        'players': players,
        'matches': matches,
        'standings': standings,
        'goals': goals,
    })


def matches_list(request):
    tournament = get_active_tournament()
    _sync_match_statuses(tournament)
    phase = request.GET.get('phase', 'GROUP')
    group_filter = request.GET.get('group', '')

    matches = (
        Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team', 'group')
        if tournament else Match.objects.none()
    )
    if phase:
        matches = matches.filter(phase=phase)
    if group_filter:
        matches = matches.filter(group__name=group_filter)

    groups = Group.objects.filter(tournament=tournament) if tournament else []
    return render(request, 'tournament/matches.html', {
        'matches': matches,
        'groups': groups,
        'phase': phase,
        'group_filter': group_filter,
        'phases': Match.PHASE_CHOICES,
    })


def match_detail(request, pk):
    _sync_match_statuses()
    match = get_object_or_404(Match, pk=pk)
    goals = match.goals.all().order_by('minute')
    home_goals = goals.filter(team=match.home_team)
    away_goals = goals.filter(team=match.away_team)
    return render(request, 'tournament/match_detail.html', {
        'match': match,
        'goals': goals,
        'home_goals': home_goals,
        'away_goals': away_goals,
        'teams': [match.home_team, match.away_team],
    })


def standings_view(request):
    tournament = get_active_tournament()
    groups_data = []
    if tournament:
        for group in Group.objects.filter(tournament=tournament).order_by('name'):
            standings = Standing.objects.filter(group=group).select_related('team').order_by(
                '-points', '-goals_for'
            )
            groups_data.append({'group': group, 'standings': standings})
    return render(request, 'tournament/standings.html', {
        'tournament': tournament,
        'groups_data': groups_data,
    })


def statistics_view(request):
    tournament = get_active_tournament()
    top_scorers = (
        Player.objects.filter(team__tournament=tournament)
        .annotate(goal_count=Count('goals', filter=Q(goals__match__tournament=tournament)))
        .filter(goal_count__gt=0)
        .order_by('-goal_count')[:10]
        if tournament
        else Player.objects.none()
    )

    teams_stats = []
    if tournament:
        for team in tournament.teams.all():
            finished_matches = Match.objects.filter(
                Q(home_team=team) | Q(away_team=team),
                status='FINISHED'
            )
            total_goals = 0
            for m in finished_matches:
                if m.home_team == team:
                    total_goals += m.home_score
                else:
                    total_goals += m.away_score
            teams_stats.append({
                'team': team,
                'goals': total_goals,
                'matches': finished_matches.count(),
            })
        teams_stats.sort(key=lambda x: x['goals'], reverse=True)

    goalkeepers = Player.objects.filter(position='GK').annotate(
        goals_conceded=Count('team__home_matches') + Count('team__away_matches')
    )

    return render(request, 'tournament/statistics.html', {
        'tournament': tournament,
        'top_scorers': top_scorers,
        'teams_stats': teams_stats[:5],
        'goalkeepers': goalkeepers,
    })


def bracket_view(request):
    tournament = get_active_tournament()
    qf_matches = KnockoutMatch.objects.filter(tournament=tournament, round='QF').order_by('match_number') if tournament else []
    sf_matches = KnockoutMatch.objects.filter(tournament=tournament, round='SF').order_by('match_number') if tournament else []
    third_match = KnockoutMatch.objects.filter(tournament=tournament, round='3RD').first() if tournament else None
    final_match = KnockoutMatch.objects.filter(tournament=tournament, round='FINAL').first() if tournament else None
    return render(request, 'tournament/bracket.html', {
        'tournament': tournament,
        'qf_matches': qf_matches,
        'sf_matches': sf_matches,
        'third_match': third_match,
        'final_match': final_match,
    })


def register_team(request):
    tournament = get_active_tournament()
    if request.method == 'POST':
        form = TeamRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('register_team_success')
    else:
        form = TeamRegistrationForm()
    return render(request, 'tournament/register_team.html', {
        'form': form,
        'tournament': tournament,
    })


def register_team_success(request):
    return render(request, 'tournament/register_team_success.html')


# ─── API endpoints (AJAX) ────────────────────────────────────

def live_scores_api(request):
    _sync_match_statuses(get_active_tournament())
    live = Match.objects.filter(status='LIVE').select_related('home_team', 'away_team')
    data = []
    for m in live:
        data.append({
            'id': m.id,
            'home': m.home_team.name,
            'away': m.away_team.name,
            'home_logo': m.home_team.logo.url if getattr(m.home_team, 'logo', None) else None,
            'away_logo': m.away_team.logo.url if getattr(m.away_team, 'logo', None) else None,
            'home_score': m.home_score,
            'away_score': m.away_score,
            'status': m.status,
            'detail_url': f'/matches/{m.id}/',
        })
    return JsonResponse({'matches': data})


def match_goals_api(request, pk):
    match = get_object_or_404(Match, pk=pk)
    goals = []
    for g in match.goals.all():
        goals.append({
            'player': g.player.full_name,
            'team': g.team.name,
            'minute': g.minute,
            'is_own_goal': g.is_own_goal,
            'is_penalty': g.is_penalty,
        })
    return JsonResponse({
        'home_score': match.home_score,
        'away_score': match.away_score,
        'status': match.status,
        'goals': goals,
    })


# ─── Admin Panel ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    tournament = get_active_tournament()
    stats = {
        'teams': Team.objects.filter(tournament=tournament).count() if tournament else 0,
        'players': Player.objects.filter(team__tournament=tournament).count() if tournament else 0,
        'matches': Match.objects.filter(tournament=tournament).count() if tournament else 0,
        'goals': Goal.objects.filter(match__tournament=tournament).count() if tournament else 0,
        'live_matches': Match.objects.filter(status='LIVE').count(),
        'finished': Match.objects.filter(status='FINISHED').count(),
    }
    recent_matches = Match.objects.filter(
        tournament=tournament, status='FINISHED'
    ).order_by('-match_date')[:5] if tournament else []
    next_matches = Match.objects.filter(
        tournament=tournament, status='SCHEDULED'
    ).order_by('match_date')[:5] if tournament else []

    return render(request, 'admin_panel/dashboard.html', {
        'tournament': tournament,
        'stats': stats,
        'recent_matches': recent_matches,
        'next_matches': next_matches,
    })


@login_required
@user_passes_test(is_admin)
def admin_teams(request):
    tournament = get_active_tournament()
    teams = Team.objects.filter(tournament=tournament).prefetch_related('players') if tournament else []
    return render(request, 'admin_panel/teams.html', {'teams': teams, 'tournament': tournament})


@login_required
@user_passes_test(is_admin)
def admin_add_team(request):
    tournament = get_active_tournament()
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            team = form.save(commit=False)
            team.tournament = tournament
            team.save()
            team.generate_qr_code()
            messages.success(request, f'Équipe "{team.name}" créée avec succès.')
            return redirect('admin_teams')
    else:
        form = TeamForm()
    return render(request, 'admin_panel/team_form.html', {'form': form, 'action': 'Ajouter'})


@login_required
@user_passes_test(is_admin)
def admin_edit_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, 'Équipe modifiée avec succès.')
            return redirect('admin_teams')
    else:
        form = TeamForm(instance=team)
    return render(request, 'admin_panel/team_form.html', {'form': form, 'team': team, 'action': 'Modifier'})


@login_required
@user_passes_test(is_admin)
def admin_delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        name = team.name
        team.delete()
        messages.success(request, f'Équipe "{name}" supprimée.')
    return redirect('admin_teams')


@login_required
@user_passes_test(is_admin)
def admin_add_player(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    if team.player_count >= 12:
        messages.error(request, 'Maximum 12 joueurs par équipe.')
        return redirect('admin_teams')
    if request.method == 'POST':
        form = PlayerForm(request.POST, request.FILES)
        if form.is_valid():
            player = form.save(commit=False)
            player.team = team
            player.save()
            messages.success(request, f'Joueur "{player.full_name}" ajouté.')
            return redirect('admin_teams')
    else:
        form = PlayerForm()
    return render(request, 'admin_panel/player_form.html', {'form': form, 'team': team})


@login_required
@user_passes_test(is_admin)
def admin_delete_player(request, pk):
    player = get_object_or_404(Player, pk=pk)
    team_pk = player.team.pk
    if request.method == 'POST':
        player.delete()
        messages.success(request, 'Joueur supprimé.')
    return redirect('admin_teams')


@login_required
@user_passes_test(is_admin)
def admin_matches(request):
    tournament = get_active_tournament()
    matches = Match.objects.filter(tournament=tournament).select_related(
        'home_team', 'away_team', 'group'
    ).order_by('match_date') if tournament else []
    return render(request, 'admin_panel/matches.html', {'matches': matches, 'tournament': tournament})


@login_required
@user_passes_test(is_admin)
def admin_add_match(request):
    tournament = get_active_tournament()
    if request.method == 'POST':
        form = MatchForm(request.POST, tournament=tournament)
        if form.is_valid():
            match = form.save(commit=False)
            match.tournament = tournament
            match.save()
            messages.success(request, 'Match ajouté avec succès.')
            return redirect('admin_matches')
    else:
        form = MatchForm(tournament=tournament)
    return render(request, 'admin_panel/match_form.html', {'form': form, 'action': 'Ajouter'})


@login_required
@user_passes_test(is_admin)
def admin_edit_match(request, pk):
    match = get_object_or_404(Match, pk=pk)
    tournament = get_active_tournament()
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match, tournament=tournament)
        if form.is_valid():
            form.save()
            messages.success(request, 'Match modifié.')
            return redirect('admin_matches')
    else:
        form = MatchForm(instance=match, tournament=tournament)
    return render(request, 'admin_panel/match_form.html', {'form': form, 'match': match, 'action': 'Modifier'})


@login_required
@user_passes_test(is_admin)
def admin_update_score(request, pk):
    match = get_object_or_404(Match, pk=pk)
    old_status = match.status
    if request.method == 'POST':
        form = ScoreUpdateForm(request.POST, instance=match)
        if form.is_valid():
            m = form.save(commit=False)
            if m.status == 'LIVE' and old_status != 'LIVE':
                m.live_started_at = timezone.now()
            m.save()
            if m.status == 'FINISHED':
                _update_standings(m)
                _check_predictions(m)
            messages.success(request, 'Score mis à jour.')
            return redirect('admin_matches')
    else:
        form = ScoreUpdateForm(instance=match)
    return render(request, 'admin_panel/score_form.html', {'form': form, 'match': match})


@login_required
@user_passes_test(is_admin)
def admin_add_goal(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    if match.status != 'LIVE':
        messages.error(request, 'Les buts ne peuvent être ajoutés que pour les matchs en direct (LIVE).')
        return redirect('admin_matches')
    if request.method == 'POST':
        form = GoalForm(request.POST, match=match)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.match = match
            goal.save()
            # Update score
            if goal.is_own_goal:
                if goal.team == match.home_team:
                    match.away_score += 1
                else:
                    match.home_score += 1
            else:
                if goal.team == match.home_team:
                    match.home_score += 1
                else:
                    match.away_score += 1
            match.save()
            if match.status == 'FINISHED':
                _update_standings(match)
            messages.success(request, f'But de {goal.player.full_name} ({goal.minute}\') enregistré.')
            return redirect('admin_matches')
    else:
        form = GoalForm(match=match)
    return render(request, 'admin_panel/goal_form.html', {'form': form, 'match': match})


@login_required
@user_passes_test(is_admin)
def admin_generate_matches(request):
    tournament = get_active_tournament()
    if not tournament:
        messages.error(request, 'Aucun tournoi actif.')
        return redirect('admin_dashboard')

    # Generate round robin for each group
    groups = Group.objects.filter(tournament=tournament)
    created = 0
    for group in groups:
        teams = list(group.teams.all())
        if len(teams) < 2:
            continue
        matchday = 1
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                if not Match.objects.filter(
                    tournament=tournament, group=group,
                    home_team=teams[i], away_team=teams[j]
                ).exists():
                    Match.objects.create(
                        tournament=tournament,
                        phase='GROUP',
                        group=group,
                        home_team=teams[i],
                        away_team=teams[j],
                        matchday=matchday,
                        venue='Terrain ADEIB, Illara'
                    )
                    created += 1
                    matchday += 1

    # Initialize standings
    for group in groups:
        for team in group.teams.all():
            Standing.objects.get_or_create(group=group, team=team)

    messages.success(request, f'{created} matchs générés avec succès.')
    return redirect('admin_matches')


@login_required
@user_passes_test(is_admin)
def admin_generate_knockout(request):
    tournament = get_active_tournament()
    if not tournament:
        messages.error(request, 'Aucun tournoi actif.')
        return redirect('admin_dashboard')

    qualified = _get_qualified_teams(tournament)
    if len(qualified) < 8:
        messages.error(request, f'Seulement {len(qualified)} équipes qualifiées (8 nécessaires).')
        return redirect('admin_dashboard')

    # Create QF matches: A1 vs B3, B1 vs C3, C1 vs A3, best 3rd vs other
    qf_pairs = [
        (qualified.get('A1'), qualified.get('B3')),
        (qualified.get('B1'), qualified.get('C3')),
        (qualified.get('C1'), qualified.get('A3')),
        (qualified.get('best3rd'), qualified.get('other3rd')),
    ]

    KnockoutMatch.objects.filter(tournament=tournament).delete()
    for i, (home, away) in enumerate(qf_pairs, 1):
        KnockoutMatch.objects.create(
            tournament=tournament,
            round='QF',
            match_number=i,
            home_team=home,
            away_team=away,
        )
    # Create empty SF and Final slots
    for i in range(1, 3):
        KnockoutMatch.objects.create(tournament=tournament, round='SF', match_number=i)
    KnockoutMatch.objects.create(tournament=tournament, round='3RD', match_number=1)
    KnockoutMatch.objects.create(tournament=tournament, round='FINAL', match_number=1)

    messages.success(request, 'Phase finale générée avec succès.')
    return redirect('bracket')


@login_required
@user_passes_test(is_admin)
def admin_knockout_score(request, pk):
    match = get_object_or_404(KnockoutMatch, pk=pk)
    if request.method == 'POST':
        form = KnockoutMatchForm(request.POST, instance=match)
        if form.is_valid():
            m = form.save()
            m.determine_winner()
            _advance_knockout(m)
            messages.success(request, 'Score éliminatoire mis à jour.')
            return redirect('bracket')
    else:
        form = KnockoutMatchForm(instance=match)
    return render(request, 'admin_panel/knockout_form.html', {'form': form, 'match': match})


@login_required
@user_passes_test(is_admin)
def admin_tournament_setup(request):
    tournament = get_active_tournament()
    if request.method == 'POST':
        if tournament:
            form = TournamentForm(request.POST, request.FILES, instance=tournament)
        else:
            form = TournamentForm(request.POST, request.FILES)
        if form.is_valid():
            t = form.save()
            # Create groups if they don't exist
            for g in ['A', 'B', 'C']:
                Group.objects.get_or_create(tournament=t, name=g)
            messages.success(request, 'Tournoi configuré avec succès.')
            return redirect('admin_dashboard')
    else:
        form = TournamentForm(instance=tournament) if tournament else TournamentForm()
    return render(request, 'admin_panel/tournament_form.html', {'form': form, 'tournament': tournament})


# ─── Helper functions ─────────────────────────────────────────

def _update_standings(match):
    if match.phase != 'GROUP' or not match.group:
        return
    for team in [match.home_team, match.away_team]:
        standing, _ = Standing.objects.get_or_create(group=match.group, team=team)
        standing.update_from_matches()


def _check_predictions(match):
    from betting.models import Prediction, PredictionLeaderboard
    for pred in match.predictions.all():
        pred.check_prediction()
        board, _ = PredictionLeaderboard.objects.get_or_create(user=pred.user)
        board.update()


def _get_qualified_teams(tournament):
    qualified = {}
    groups_thirds = []

    for group in Group.objects.filter(tournament=tournament).order_by('name'):
        standings = Standing.objects.filter(group=group).order_by('-points', '-goals_for')
        teams = list(standings)
        if len(teams) >= 1:
            qualified[f'{group.name}1'] = teams[0].team
        if len(teams) >= 2:
            qualified[f'{group.name}2'] = teams[1].team
        if len(teams) >= 3:
            groups_thirds.append(teams[2])

    # Best 2 thirds
    groups_thirds.sort(key=lambda s: (-s.points, -s.goal_difference, -s.goals_for))
    if len(groups_thirds) >= 2:
        qualified['best3rd'] = groups_thirds[0].team
        qualified['other3rd'] = groups_thirds[1].team

    return qualified


def _advance_knockout(match):
    if match.status != 'FINISHED' or not match.winner:
        return
    loser = match.home_team if match.winner == match.away_team else match.away_team

    if match.round == 'QF':
        qf_matches = KnockoutMatch.objects.filter(
            tournament=match.tournament, round='QF', status='FINISHED'
        ).order_by('match_number')
        sf_matches = list(KnockoutMatch.objects.filter(
            tournament=match.tournament, round='SF'
        ).order_by('match_number'))
        winners = [m.winner for m in qf_matches]
        for i, w in enumerate(winners):
            sf_idx = i // 2
            if sf_idx < len(sf_matches):
                sf = sf_matches[sf_idx]
                if i % 2 == 0:
                    sf.home_team = w
                else:
                    sf.away_team = w
                sf.save()

    elif match.round == 'SF':
        sf_all = KnockoutMatch.objects.filter(
            tournament=match.tournament, round='SF', status='FINISHED'
        )
        final = KnockoutMatch.objects.filter(tournament=match.tournament, round='FINAL').first()
        third = KnockoutMatch.objects.filter(tournament=match.tournament, round='3RD').first()
        if final and sf_all.count() >= 1:
            sf_list = list(sf_all.order_by('match_number'))
            if len(sf_list) >= 1 and sf_list[0].winner:
                final.home_team = sf_list[0].winner
            if len(sf_list) >= 2 and sf_list[1].winner:
                final.away_team = sf_list[1].winner
            final.save()
        # 3rd place: losers of SF
        if third:
            sf_finished = KnockoutMatch.objects.filter(
                tournament=match.tournament, round='SF', status='FINISHED'
            ).order_by('match_number')
            losers = []
            for sf in sf_finished:
                l = sf.home_team if sf.winner == sf.away_team else sf.away_team
                losers.append(l)
            if len(losers) >= 1:
                third.home_team = losers[0]
            if len(losers) >= 2:
                third.away_team = losers[1]
            third.save()


# Ticket Management Views

@login_required
@user_passes_test(is_admin)
def admin_tickets(request):
    """Liste des configurations de tickets par match"""
    tournament = get_active_tournament()
    matches = Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team').prefetch_related('ticket_config')
    return render(request, 'admin_panel/tickets.html', {
        'matches': matches,
        'tournament': tournament,
    })


@login_required
@user_passes_test(is_admin)
def admin_ticket_config(request, match_pk):
    """Configurer les tickets pour un match"""
    match = get_object_or_404(Match, pk=match_pk)
    config, created = TicketConfig.objects.get_or_create(
        match=match,
        defaults={
            'price': 500,
            'ticket_size': 'small',
            'quantity': 100,
        }
    )

    if request.method == 'POST':
        form = TicketConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuration des tickets mise à jour.')
            return redirect('admin_tickets')
    else:
        form = TicketConfigForm(instance=config)

    return render(request, 'admin_panel/ticket_config.html', {
        'form': form,
        'match': match,
        'config': config,
    })


@login_required
@user_passes_test(is_admin)
def admin_generate_tickets(request, config_pk):
    """Generer les tickets en PDF"""
    config = get_object_or_404(TicketConfig, pk=config_pk)
    match = config.match

    if request.method == 'POST':
        # Supprimer les anciens tickets si demande
        if request.POST.get('regenerate') == 'true':
            config.tickets.all().delete()

        # Generer les donnees des tickets
        existing_count = config.tickets.count()
        quantity_to_generate = config.quantity - existing_count

        if quantity_to_generate <= 0:
            messages.warning(request, 'Tous les tickets sont déjà générés.')
            return redirect('admin_download_tickets', config_pk=config.pk)

        # Creer les tickets en base
        tickets_data = []
        for i in range(quantity_to_generate):
            ticket_num = f"{match.id:03d}-{existing_count + i + 1:04d}"
            seat_num = f"{chr(65 + (existing_count + i) // 20)}{(existing_count + i) % 20 + 1:02d}"

            ticket = Ticket.objects.create(
                config=config,
                ticket_number=ticket_num,
                seat_number=seat_num,
            )

            tickets_data.append({
                'ticket_number': ticket_num,
                'seat_number': seat_num,
                'home_team': match.home_team.name,
                'away_team': match.away_team.name,
                'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE',
                'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
                'gate_closes': str(config.gate_closes)[:5] if config.gate_closes else '19:00',
                'venue': match.venue or 'Terrain ADEIB, Illara',
                'price': config.price,
                'currency': config.currency,
            })

        # Generer le PDF
        pdf_buffer = generate_tickets_pdf(match, config, tickets_data)

        # Nom du fichier
        filename = f"tickets_{match.home_team.name}_vs_{match.away_team.name}_{config.ticket_size}.pdf".replace(' ', '_')

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, f'{quantity_to_generate} tickets générés avec succès.')
        return response

    return render(request, 'admin_panel/generate_tickets_confirm.html', {
        'config': config,
        'match': match,
        'existing_count': config.tickets.count(),
    })


@login_required
@user_passes_test(is_admin)
def admin_download_tickets(request, config_pk):
    """Telecharger les tickets déjà générés"""
    config = get_object_or_404(TicketConfig, pk=config_pk)
    match = config.match

    tickets = config.tickets.all()
    if not tickets.exists():
        messages.error(request, 'Aucun ticket généré pour ce match.')
        return redirect('admin_ticket_config', match_pk=match.pk)

    tickets_data = []
    for ticket in tickets:
        tickets_data.append({
            'ticket_number': ticket.ticket_number,
            'seat_number': ticket.seat_number,
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'match_date': match.match_date.strftime('%d/%m/%Y') if match.match_date else 'DATE',
            'gate_opens': str(config.gate_opens)[:5] if config.gate_opens else '13:00',
            'gate_closes': str(config.gate_closes)[:5] if config.gate_closes else '19:00',
            'venue': match.venue or 'Terrain ADEIB, Illara',
            'price': config.price,
            'currency': config.currency,
        })

    pdf_buffer = generate_tickets_pdf(match, config, tickets_data)

    filename = f"tickets_{match.home_team.name}_vs_{match.away_team.name}_{config.ticket_size}.pdf".replace(' ', '_')

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@user_passes_test(is_admin)
def admin_preview_ticket(request, config_pk):
    """Aperçu d'un ticket unique"""
    config = get_object_or_404(TicketConfig, pk=config_pk)
    match = config.match

    pdf_buffer = generate_ticket_preview(match, config)

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ticket_preview.pdf"'
    return response


@login_required
@user_passes_test(is_admin)
def admin_delete_tickets(request, config_pk):
    """Supprimer tous les tickets d'une configuration"""
    config = get_object_or_404(TicketConfig, pk=config_pk)
    match = config.match

    if request.method == 'POST':
        count = config.tickets.count()
        config.tickets.all().delete()
        messages.success(request, f'{count} tickets supprimés.')
        return redirect('admin_tickets')

    return render(request, 'admin_panel/delete_tickets_confirm.html', {
        'config': config,
        'match': match,
        'ticket_count': config.tickets.count(),
    })


# ─── NOUVEAUX VUES POUR TICKETS COOL ET UNIQUES ───────────────────────────

@login_required
@user_passes_test(is_admin)
def admin_preview_cool_ticket(request, match_pk):
    """Aperçu d'un ticket au design cool et unique"""
    match = get_object_or_404(Match, pk=match_pk)

    # Créer une config temporaire si elle n'existe pas
    config, _ = TicketConfig.objects.get_or_create(
        match=match,
        defaults={
            'price': 500,
            'ticket_size': 'cool',
            'quantity': 100,
        }
    )

    # Générer le PDF cool
    pdf_buffer = generate_cool_ticket_pdf(match, config, is_preview=True)

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="ticket_cool_preview.pdf"'
    return response


@login_required
@user_passes_test(is_admin)
def admin_generate_cool_tickets(request, match_pk):
    """Générer des tickets au design cool et unique"""
    match = get_object_or_404(Match, pk=match_pk)

    config, _ = TicketConfig.objects.get_or_create(
        match=match,
        defaults={
            'price': 500,
            'ticket_size': 'cool',
            'quantity': 100,
        }
    )

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 8))

        # Générer les tickets en PDF bulk
        pdf_buffer = generate_bulk_cool_tickets(match, config, quantity)

        filename = f"tickets_cool_{match.home_team.name}_vs_{match.away_team.name}.pdf".replace(' ', '_')

        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        messages.success(request, f'{quantity} tickets cool générés avec succès.')
        return response

    return render(request, 'admin_panel/generate_cool_tickets.html', {
        'match': match,
        'config': config,
    })


@login_required
@user_passes_test(is_admin)
def admin_download_individual_cool_ticket(request, ticket_pk):
    """Télécharger un ticket individuel au format cool"""
    ticket = get_object_or_404(Ticket, pk=ticket_pk)

    pdf_buffer = generate_ticket_from_model(ticket)

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.ticket_number}.pdf"'
    return response


@login_required
@user_passes_test(is_admin)
def admin_ticket_designer(request):
    """Page principale du designer de tickets"""
    tournament = get_active_tournament()
    matches = Match.objects.filter(tournament=tournament).select_related('home_team', 'away_team').prefetch_related('ticket_config')

    return render(request, 'admin_panel/ticket_designer.html', {
        'matches': matches,
        'tournament': tournament,
    })
