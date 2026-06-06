from django import forms
from .models import Team, Player, Match, Goal, Standing, KnockoutMatch, Tournament, Group, TeamRegistration, TicketConfig


class TeamRegistrationForm(forms.ModelForm):
    class Meta:
        model = TeamRegistration
        fields = ['team_name', 'captain_name', 'phone', 'email', 'neighborhood', 'player_count', 'payment_proof', 'notes']
        widgets = {
            'team_name':    forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Les Lions d\'Illara'}),
            'captain_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom et nom'}),
            'phone':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+229 ...'}),
            'email':        forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'optionnel'}),
            'neighborhood': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Quartier Centre'}),
            'player_count': forms.NumberInput(attrs={'class': 'form-input', 'min': 7, 'max': 18}),
            'notes':        forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Informations complémentaires...'}),
        }


class TournamentForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = ['name', 'edition', 'start_date', 'end_date', 'location',
                  'description', 'logo', 'qualifiers_per_group']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'qualifiers_per_group': forms.NumberInput(attrs={'min': 1, 'max': 4}),
        }


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'logo', 'group', 'coach_name', 'president_name']
        labels = {
            'coach_name': 'Entraîneur (optionnel)',
            'president_name': 'Président (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].queryset = Group.objects.all()
        self.fields['group'].required = False
        self.fields['coach_name'].required = False
        self.fields['president_name'].required = False


class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['first_name', 'last_name', 'nickname', 'age', 'position',
                  'jersey_number', 'photo', 'is_captain', 'yellow_cards', 'red_cards']
        widgets = {
            'age': forms.NumberInput(attrs={'min': 15, 'max': 40}),
            'jersey_number': forms.NumberInput(attrs={'min': 1, 'max': 99}),
            'yellow_cards': forms.NumberInput(attrs={'min': 0, 'max': 50}),
            'red_cards': forms.NumberInput(attrs={'min': 0, 'max': 20}),
        }
        labels = {
            'nickname': 'Surnom (nom de maillot)',
            'yellow_cards': 'Cartons jaunes',
            'red_cards': 'Cartons rouges',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].required = False


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['phase', 'group', 'home_team', 'away_team', 'match_date', 'venue',
                  'matchday', 'status', 'stream_platform', 'stream_url']
        widgets = {
            'match_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'stream_url': forms.URLInput(attrs={'placeholder': 'https://youtube.com/watch?v=...'}),
        }

    def __init__(self, *args, tournament=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tournament:
            self.fields['home_team'].queryset = Team.objects.filter(tournament=tournament)
            self.fields['away_team'].queryset = Team.objects.filter(tournament=tournament)
            self.fields['group'].queryset = Group.objects.filter(tournament=tournament)
        self.fields['group'].required = False

    def clean(self):
        cleaned = super().clean()
        home = cleaned.get('home_team')
        away = cleaned.get('away_team')
        if home and away and home == away:
            raise forms.ValidationError("Les deux équipes doivent être différentes.")
        return cleaned


class ScoreUpdateForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['home_score', 'away_score', 'status', 'man_of_the_match']
        widgets = {
            'home_score': forms.NumberInput(attrs={'min': 0}),
            'away_score': forms.NumberInput(attrs={'min': 0}),
        }
        labels = {
            'man_of_the_match': 'Homme du match',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['man_of_the_match'].required = False
        if self.instance and self.instance.pk:
            self.fields['man_of_the_match'].queryset = Player.objects.filter(
                team__in=[self.instance.home_team, self.instance.away_team]
            )


class MatchLiveForm(forms.ModelForm):
    """Passer un match en direct et renseigner le lien de diffusion."""
    class Meta:
        model = Match
        fields = ['stream_platform', 'stream_url']
        widgets = {
            'stream_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://youtube.com/watch?v=...',
            }),
        }
        labels = {
            'stream_platform': 'Plateforme',
            'stream_url': 'Lien du direct',
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['player', 'team', 'minute', 'is_own_goal', 'is_penalty']
        widgets = {
            'minute': forms.NumberInput(attrs={'min': 1, 'max': 120}),
        }

    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        if match:
            teams = [match.home_team, match.away_team]
            self.fields['team'].queryset = Team.objects.filter(pk__in=[t.pk for t in teams])
            self.fields['player'].queryset = Player.objects.filter(team__in=teams)


class KnockoutMatchForm(forms.ModelForm):
    class Meta:
        model = KnockoutMatch
        fields = ['home_team', 'away_team', 'home_score', 'away_score',
                  'home_penalties', 'away_penalties', 'status', 'match_date', 'venue']
        widgets = {
            'match_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'home_score': forms.NumberInput(attrs={'min': 0}),
            'away_score': forms.NumberInput(attrs={'min': 0}),
            'home_penalties': forms.NumberInput(attrs={'min': 0}),
            'away_penalties': forms.NumberInput(attrs={'min': 0}),
        }


class TicketConfigForm(forms.ModelForm):
    class Meta:
        model = TicketConfig
        fields = ['price', 'currency', 'quantity', 'gate_opens', 'gate_closes', 'ticket_text', 'is_active']
        widgets = {
            'price': forms.NumberInput(attrs={'min': 0, 'step': 50}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'max': 10000}),
            'gate_opens': forms.TimeInput(attrs={'type': 'time'}),
            'gate_closes': forms.TimeInput(attrs={'type': 'time'}),
            'ticket_text': forms.TextInput(attrs={'placeholder': 'Ex: Match important - places numérotées'}),
        }
        labels = {
            'price': 'Prix du ticket',
            'currency': 'Devise',
            'quantity': 'Quantité à générer',
            'gate_opens': 'Ouverture des portes',
            'gate_closes': 'Fermeture des portes',
            'ticket_text': 'Texte additionnel sur les tickets',
            'is_active': 'Actif',
        }
