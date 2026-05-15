from django.db import models
from django.contrib.auth.models import User
import qrcode
import io
from django.core.files.base import ContentFile


class Tournament(models.Model):
    name = models.CharField(max_length=200, default='ADEIB U26 Illara')
    edition = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='tournament/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tournoi'


class Group(models.Model):
    GROUP_CHOICES = [('A', 'Groupe A'), ('B', 'Groupe B'), ('C', 'Groupe C')]
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=1, choices=GROUP_CHOICES)

    def __str__(self):
        return f'Groupe {self.name}'

    class Meta:
        verbose_name = 'Groupe'
        ordering = ['name']


class Team(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='teams/', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f'Équipe: {self.name} | Tournoi: ADEIB U26 Illara')
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        filename = f'qr_{self.name.replace(" ", "_")}.png'
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=True)

    @property
    def player_count(self):
        return self.players.count()

    class Meta:
        verbose_name = 'Équipe'
        ordering = ['name']


class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Gardien'),
        ('DEF', 'Défenseur'),
        ('MID', 'Milieu'),
        ('FWD', 'Attaquant'),
    ]
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    position = models.CharField(max_length=3, choices=POSITION_CHOICES, default='MID')
    jersey_number = models.PositiveIntegerField(null=True, blank=True)
    photo = models.ImageField(upload_to='players/', blank=True, null=True)
    is_captain = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def goals_count(self):
        return self.goals.count()

    class Meta:
        verbose_name = 'Joueur'
        ordering = ['last_name', 'first_name']


class Match(models.Model):
    PHASE_CHOICES = [
        ('GROUP', 'Phase de groupes'),
        ('QF', 'Quart de finale'),
        ('SF', 'Demi-finale'),
        ('3RD', 'Match 3e place'),
        ('FINAL', 'Finale'),
    ]
    STATUS_CHOICES = [
        ('SCHEDULED', 'Programmé'),
        ('LIVE', 'En direct'),
        ('FINISHED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, default='GROUP')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    match_date = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True, default='Terrain ADEIB, Illara')
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    matchday = models.PositiveIntegerField(default=1)
    live_started_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.home_team} vs {self.away_team}'

    @property
    def result(self):
        if self.status == 'FINISHED':
            if self.home_score > self.away_score:
                return 'HOME'
            elif self.away_score > self.home_score:
                return 'AWAY'
            return 'DRAW'
        return None

    @property
    def score_display(self):
        if self.status in ['LIVE', 'FINISHED']:
            return f'{self.home_score} - {self.away_score}'
        return 'vs'

    class Meta:
        verbose_name = 'Match'
        verbose_name_plural = 'Matchs'
        ordering = ['match_date']


class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals_scored')
    minute = models.PositiveIntegerField()
    is_own_goal = models.BooleanField(default=False)
    is_penalty = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        og = ' (CSC)' if self.is_own_goal else ''
        p = ' (P)' if self.is_penalty else ''
        return f'{self.player} {self.minute}\' {og}{p}'

    class Meta:
        verbose_name = 'But'
        ordering = ['minute']


class Standing(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='standings')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='standings')
    played = models.PositiveIntegerField(default=0)
    won = models.PositiveIntegerField(default=0)
    drawn = models.PositiveIntegerField(default=0)
    lost = models.PositiveIntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against

    def update_from_matches(self):
        from django.db.models import Q
        matches = Match.objects.filter(
            Q(home_team=self.team) | Q(away_team=self.team),
            group=self.group,
            status='FINISHED'
        )
        self.played = matches.count()
        self.won = self.drawn = self.lost = 0
        self.goals_for = self.goals_against = self.points = 0

        for match in matches:
            if match.home_team == self.team:
                self.goals_for += match.home_score
                self.goals_against += match.away_score
                if match.home_score > match.away_score:
                    self.won += 1; self.points += 3
                elif match.home_score == match.away_score:
                    self.drawn += 1; self.points += 1
                else:
                    self.lost += 1
            else:
                self.goals_for += match.away_score
                self.goals_against += match.home_score
                if match.away_score > match.home_score:
                    self.won += 1; self.points += 3
                elif match.away_score == match.home_score:
                    self.drawn += 1; self.points += 1
                else:
                    self.lost += 1
        self.save()

    def __str__(self):
        return f'{self.team} - Groupe {self.group.name}'

    class Meta:
        verbose_name = 'Classement'
        ordering = ['-points', '-goals_for']
        unique_together = ['group', 'team']


class KnockoutMatch(models.Model):
    ROUND_CHOICES = [
        ('QF', 'Quart de finale'),
        ('SF', 'Demi-finale'),
        ('3RD', 'Match 3e place'),
        ('FINAL', 'Finale'),
    ]
    STATUS_CHOICES = [
        ('SCHEDULED', 'Programmé'),
        ('LIVE', 'En direct'),
        ('FINISHED', 'Terminé'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='knockout_matches')
    round = models.CharField(max_length=10, choices=ROUND_CHOICES)
    match_number = models.PositiveIntegerField(default=1)
    home_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='knockout_home')
    away_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='knockout_away')
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    home_penalties = models.PositiveIntegerField(null=True, blank=True)
    away_penalties = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SCHEDULED')
    match_date = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True, default='Terrain ADEIB, Illara')
    winner = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='knockout_wins')

    def __str__(self):
        ht = self.home_team.name if self.home_team else 'TBD'
        at = self.away_team.name if self.away_team else 'TBD'
        return f'{self.get_round_display()}: {ht} vs {at}'

    def determine_winner(self):
        if self.status == 'FINISHED':
            if self.home_score > self.away_score:
                self.winner = self.home_team
            elif self.away_score > self.home_score:
                self.winner = self.away_team
            elif self.home_penalties is not None and self.away_penalties is not None:
                if self.home_penalties > self.away_penalties:
                    self.winner = self.home_team
                else:
                    self.winner = self.away_team
            self.save()

    class Meta:
        verbose_name = 'Match éliminatoire'
        ordering = ['round', 'match_number']


class TeamRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING',  'En attente'),
        ('APPROVED', 'Approuvée'),
        ('REJECTED', 'Refusée'),
    ]

    team_name      = models.CharField(max_length=200, verbose_name='Nom de l\'équipe')
    captain_name   = models.CharField(max_length=200, verbose_name='Nom du capitaine')
    phone          = models.CharField(max_length=20,  verbose_name='Téléphone')
    email          = models.EmailField(blank=True,    verbose_name='Email (optionnel)')
    neighborhood   = models.CharField(max_length=200, verbose_name='Quartier / Village')
    player_count   = models.PositiveIntegerField(default=11, verbose_name='Nombre de joueurs')
    payment_proof  = models.ImageField(upload_to='registrations/', verbose_name='Preuve de paiement')
    notes          = models.TextField(blank=True, verbose_name='Remarques')
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    submitted_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.team_name} — {self.get_status_display()}'

    class Meta:
        verbose_name = 'Inscription équipe'
        verbose_name_plural = 'Inscriptions équipes'
        ordering = ['-submitted_at']


class TicketConfig(models.Model):
    """Configuration de génération de tickets pour un match"""
    TICKET_SIZES = [
        ('small', 'Petit (10 par page)'),
        ('medium', 'Moyen (6 par page)'),
        ('large', 'Grand (4 par page)'),
        ('premium', 'Premium A4 Paysage (2 par page)'),
    ]

    CURRENCY_CHOICES = [
        ('NGN', 'Naira (₦)'),
        ('XOF', 'FCFA (CFA)'),
    ]

    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name='ticket_config')
    price = models.DecimalField(max_digits=10, decimal_places=0, default=500, verbose_name='Prix')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='XOF', verbose_name='Devise')
    ticket_size = models.CharField(max_length=10, choices=TICKET_SIZES, default='small')
    quantity = models.PositiveIntegerField(default=100, verbose_name='Quantité à générer')
    gate_opens = models.TimeField(default='13:00', verbose_name='Ouverture des portes')
    gate_closes = models.TimeField(default='19:00', verbose_name='Fermeture des portes')
    ticket_text = models.CharField(max_length=200, blank=True, verbose_name='Texte additionnel')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Tickets {self.match} - {self.quantity} unités'

    @property
    def currency_symbol(self):
        if self.currency == 'NGN':
            return '₦'
        return 'CFA'

    @property
    def price_display(self):
        return f"{self.currency_symbol} {self.price:,.0f}"

    class Meta:
        verbose_name = 'Configuration tickets'
        verbose_name_plural = 'Configurations tickets'


class Ticket(models.Model):
    """Ticket individuel généré"""
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponible'),
        ('SOLD', 'Vendu'),
        ('USED', 'Utilisé'),
        ('CANCELLED', 'Annulé'),
    ]

    config = models.ForeignKey(TicketConfig, on_delete=models.CASCADE, related_name='tickets')
    ticket_number = models.CharField(max_length=20, unique=True)
    seat_number = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='AVAILABLE')
    generated_at = models.DateTimeField(auto_now_add=True)
    sold_at = models.DateTimeField(null=True, blank=True)
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'Ticket {self.ticket_number}'

    class Meta:
        verbose_name = 'Ticket'
        ordering = ['ticket_number']
