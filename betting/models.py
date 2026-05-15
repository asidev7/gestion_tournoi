from django.db import models
from django.contrib.auth.models import User
from tournament.models import Match


class Prediction(models.Model):
    PREDICTION_CHOICES = [
        ('1', 'Victoire équipe A'),
        ('X', 'Match nul'),
        ('2', 'Victoire équipe B'),
        ('1X', 'Victoire A ou Nul'),
        ('X2', 'Nul ou Victoire B'),
        ('12', 'Victoire A ou B'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='predictions')
    prediction = models.CharField(max_length=2, choices=PREDICTION_CHOICES)
    odds = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def check_prediction(self):
        match = self.match
        if match.status != 'FINISHED':
            return None
        result = match.result
        pred = self.prediction
        if pred == '1' and result == 'HOME':
            self.is_correct = True
        elif pred == 'X' and result == 'DRAW':
            self.is_correct = True
        elif pred == '2' and result == 'AWAY':
            self.is_correct = True
        elif pred == '1X' and result in ['HOME', 'DRAW']:
            self.is_correct = True
        elif pred == 'X2' and result in ['DRAW', 'AWAY']:
            self.is_correct = True
        elif pred == '12' and result in ['HOME', 'AWAY']:
            self.is_correct = True
        else:
            self.is_correct = False
        self.save()
        return self.is_correct

    def __str__(self):
        return f'{self.user} - {self.match} - {self.prediction}'

    class Meta:
        verbose_name = 'Pronostic'
        unique_together = ['user', 'match']
        ordering = ['-created_at']


class PredictionLeaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard')
    total_predictions = models.PositiveIntegerField(default=0)
    correct_predictions = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    @property
    def success_rate(self):
        if self.total_predictions == 0:
            return 0
        return round((self.correct_predictions / self.total_predictions) * 100, 1)

    def update(self):
        preds = Prediction.objects.filter(user=self.user, is_correct__isnull=False)
        self.total_predictions = preds.count()
        self.correct_predictions = preds.filter(is_correct=True).count()
        self.points = self.correct_predictions * 10
        self.save()

    def __str__(self):
        return f'{self.user} - {self.points} pts'

    class Meta:
        verbose_name = 'Classement pronostics'
        ordering = ['-points']
