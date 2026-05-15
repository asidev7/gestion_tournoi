from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Group, Match, Standing, Team, Tournament


class HomeLiveSyncTests(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name='ADEIB U26 Illara',
            edition='2026',
            is_active=True,
        )
        self.group = Group.objects.create(tournament=self.tournament, name='A')
        self.home_team = Team.objects.create(
            tournament=self.tournament,
            group=self.group,
            name='Illara FC',
        )
        self.away_team = Team.objects.create(
            tournament=self.tournament,
            group=self.group,
            name='Winners FC',
        )

    def test_home_switches_started_match_to_live(self):
        started_at = timezone.now() - timedelta(minutes=5)
        match = Match.objects.create(
            tournament=self.tournament,
            group=self.group,
            home_team=self.home_team,
            away_team=self.away_team,
            match_date=started_at,
            status='SCHEDULED',
        )

        response = self.client.get(reverse('home'))

        match.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.status, 'LIVE')
        self.assertEqual(response.context['live_matches'].count(), 1)

    def test_live_scores_api_finishes_overdue_live_match(self):
        long_running_start = timezone.now() - timedelta(minutes=120)
        standing = Standing.objects.create(group=self.group, team=self.home_team)
        Standing.objects.create(group=self.group, team=self.away_team)
        match = Match.objects.create(
            tournament=self.tournament,
            group=self.group,
            home_team=self.home_team,
            away_team=self.away_team,
            match_date=long_running_start,
            live_started_at=long_running_start,
            home_score=2,
            away_score=1,
            status='LIVE',
        )

        response = self.client.get(reverse('live_scores_api'))

        match.refresh_from_db()
        standing.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(match.status, 'FINISHED')
        self.assertEqual(response.json()['matches'], [])
        self.assertEqual(standing.points, 3)


class TeamDetailTemplateTests(TestCase):
    def test_team_detail_page_renders_without_template_error(self):
        tournament = Tournament.objects.create(name='ADEIB U26 Illara', is_active=True)
        group = Group.objects.create(tournament=tournament, name='A')
        team = Team.objects.create(tournament=tournament, group=group, name='Illara FC')
        opponent = Team.objects.create(tournament=tournament, group=group, name='Rivals FC')
        Standing.objects.create(group=group, team=team, points=4, played=2, won=1, drawn=1, goals_for=3, goals_against=1)
        Match.objects.create(
            tournament=tournament,
            group=group,
            home_team=team,
            away_team=opponent,
            match_date=timezone.now() + timedelta(days=1),
            status='SCHEDULED',
        )

        response = self.client.get(reverse('team_detail', args=[team.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Illara FC')
