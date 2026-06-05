import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from betting.models import Prediction, PredictionLeaderboard
from tournament.models import (
    Goal,
    Group,
    KnockoutMatch,
    Match,
    Player,
    Standing,
    Team,
    Tournament,
)


class Command(BaseCommand):
    help = "Seed demo data for all models (tournament + betting). Safe to re-run."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete tournament/betting data before seeding (keeps auth users).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        force = options["force"]

        if force:
            Goal.objects.all().delete()
            Prediction.objects.all().delete()
            PredictionLeaderboard.objects.all().delete()
            Standing.objects.all().delete()
            Match.objects.all().delete()
            KnockoutMatch.objects.all().delete()
            Player.objects.all().delete()
            Team.objects.all().delete()
            Group.objects.all().delete()
            Tournament.objects.all().delete()

        random.seed(26)

        tournament, _ = Tournament.objects.get_or_create(
            name="Cup Legends",
            defaults={
                "edition": "Saison 2026",
                "location": "Illara",
                "description": "Tournoi de football Cup Legends — données de démonstration.",
                "is_active": True,
            },
        )
        if not tournament.is_active:
            tournament.is_active = True
            tournament.save(update_fields=["is_active"])

        for g in ["A", "B", "C"]:
            Group.objects.get_or_create(tournament=tournament, name=g)

        groups = {g.name: g for g in Group.objects.filter(tournament=tournament)}

        # Teams
        team_names = {
            "A": ["Illara FC", "City Lions", "Jeunes Espoirs", "Étoiles d'Or"],
            "B": ["Royal United", "Académie Nord", "Sporting Porto", "Les Aigles"],
            "C": ["Olympic Sud", "River Plate", "Atlas FC", "Phoenix Club"],
        }

        teams_by_group = {}
        for group_name, names in team_names.items():
            group = groups[group_name]
            teams = []
            for name in names:
                team, _ = Team.objects.get_or_create(tournament=tournament, name=name, defaults={"group": group})
                if team.group_id != group.id:
                    team.group = group
                    team.save(update_fields=["group"])
                teams.append(team)
            teams_by_group[group_name] = teams

        # Players
        first_names = ["Jean", "Marc", "Paul", "David", "Koffi", "Sami", "Ousmane", "Junior", "Eric", "Noah", "Kevin"]
        last_names = ["Ahouansou", "Mensah", "Diallo", "Traore", "Hounkpe", "Kouassi", "Adje", "Sossa", "Akindele"]
        positions = ["GK", "DEF", "MID", "FWD"]

        for group_teams in teams_by_group.values():
            for team in group_teams:
                existing = Player.objects.filter(team=team).count()
                target = 12
                if existing >= target:
                    continue
                used_numbers = set(
                    Player.objects.filter(team=team, jersey_number__isnull=False).values_list("jersey_number", flat=True)
                )
                for i in range(existing, target):
                    pos = "GK" if i == 0 else random.choices(positions, weights=[1, 4, 4, 3])[0]
                    jersey = None
                    for n in range(1, 100):
                        if n not in used_numbers:
                            jersey = n
                            used_numbers.add(n)
                            break
                    Player.objects.create(
                        team=team,
                        first_name=random.choice(first_names),
                        last_name=random.choice(last_names),
                        age=random.randint(16, 26),
                        position=pos,
                        jersey_number=jersey,
                        is_captain=(i == 1),
                    )

        # Matches (round robin within each group)
        now = timezone.now()
        finished_scores = [(2, 0), (1, 1), (0, 1), (3, 2), (0, 0)]

        created_matches = 0
        for group_name, group in groups.items():
            teams = teams_by_group.get(group_name, [])
            matchday = 1
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    home = teams[i]
                    away = teams[j]
                    match, created = Match.objects.get_or_create(
                        tournament=tournament,
                        phase="GROUP",
                        group=group,
                        home_team=home,
                        away_team=away,
                        defaults={
                            "matchday": matchday,
                            "match_date": now + timedelta(days=matchday),
                            "venue": "Stade Cup Legends",
                            "status": "SCHEDULED",
                        },
                    )
                    if created:
                        created_matches += 1
                    matchday += 1

        # Mark a subset as finished with goals
        group_matches = list(Match.objects.filter(tournament=tournament, phase="GROUP").order_by("id"))
        to_finish = group_matches[: min(12, len(group_matches))]
        for idx, match in enumerate(to_finish):
            home_score, away_score = finished_scores[idx % len(finished_scores)]
            if match.status != "FINISHED" or match.home_score != home_score or match.away_score != away_score:
                match.status = "FINISHED"
                match.home_score = home_score
                match.away_score = away_score
                match.match_date = match.match_date or (now - timedelta(days=idx + 1))
                match.save(update_fields=["status", "home_score", "away_score", "match_date"])

            # ensure goals match the score
            Goal.objects.filter(match=match).delete()
            minute = 5
            home_players = list(Player.objects.filter(team=match.home_team))
            away_players = list(Player.objects.filter(team=match.away_team))
            for _ in range(home_score):
                Goal.objects.create(
                    match=match,
                    player=random.choice(home_players),
                    team=match.home_team,
                    minute=minute,
                )
                minute += random.randint(4, 13)
            for _ in range(away_score):
                Goal.objects.create(
                    match=match,
                    player=random.choice(away_players),
                    team=match.away_team,
                    minute=minute,
                )
                minute += random.randint(4, 13)

        # Standings
        for group in groups.values():
            for team in Team.objects.filter(tournament=tournament, group=group):
                standing, _ = Standing.objects.get_or_create(group=group, team=team)
                standing.update_from_matches()

        # Knockout (basic bracket based on standings; safe even if not enough teams)
        qualified = []
        for group in Group.objects.filter(tournament=tournament).order_by("name"):
            standings = list(Standing.objects.filter(group=group).select_related("team").order_by("-points", "-goals_for"))
            qualified.extend([s.team for s in standings[:2]])

        KnockoutMatch.objects.get_or_create(tournament=tournament, round="FINAL", match_number=1)
        KnockoutMatch.objects.get_or_create(tournament=tournament, round="3RD", match_number=1)
        for i in range(1, 3):
            KnockoutMatch.objects.get_or_create(tournament=tournament, round="SF", match_number=i)
        for i in range(1, 5):
            KnockoutMatch.objects.get_or_create(tournament=tournament, round="QF", match_number=i)

        qfs = list(KnockoutMatch.objects.filter(tournament=tournament, round="QF").order_by("match_number"))
        for i, qf in enumerate(qfs):
            home = qualified[i] if i < len(qualified) else None
            away = qualified[i + 4] if (i + 4) < len(qualified) else None
            if qf.home_team_id != (home.id if home else None) or qf.away_team_id != (away.id if away else None):
                qf.home_team = home
                qf.away_team = away
                qf.status = "SCHEDULED"
                qf.home_score = 0
                qf.away_score = 0
                qf.save(update_fields=["home_team", "away_team", "status", "home_score", "away_score"])

        # Betting: create demo users + predictions
        users = []
        for username in ["demo1", "demo2", "demo3"]:
            user, _ = User.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            users.append(user)

        sample_matches = list(Match.objects.filter(tournament=tournament).order_by("id")[:10])
        pred_choices = ["1", "X", "2", "1X", "X2", "12"]
        for user in users:
            for match in sample_matches:
                pred, _ = Prediction.objects.get_or_create(
                    user=user,
                    match=match,
                    defaults={
                        "prediction": random.choice(pred_choices),
                        "odds": round(random.uniform(1.2, 3.4), 2),
                    },
                )
                if match.status == "FINISHED":
                    pred.check_prediction()
            board, _ = PredictionLeaderboard.objects.get_or_create(user=user)
            board.update()

        self.stdout.write(self.style.SUCCESS("Seed OK"))
        self.stdout.write(f"- Tournament: {tournament.name}")
        self.stdout.write(f"- Teams: {Team.objects.filter(tournament=tournament).count()}")
        self.stdout.write(f"- Players: {Player.objects.filter(team__tournament=tournament).count()}")
        self.stdout.write(f"- Matches: {Match.objects.filter(tournament=tournament).count()} (created {created_matches})")
        self.stdout.write(f"- Predictions: {Prediction.objects.count()}")

