from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from tournament.models import Match
from .models import Prediction, PredictionLeaderboard
from .forms import PredictionForm


@login_required
def predictions_list(request):
    upcoming = Match.objects.filter(status='SCHEDULED').order_by('match_date')
    user_preds = {p.match_id: p for p in Prediction.objects.filter(user=request.user)}
    matches_data = []
    for match in upcoming:
        pred = user_preds.get(match.pk)
        matches_data.append({'match': match, 'prediction': pred})

    leaderboard = PredictionLeaderboard.objects.all().select_related('user').order_by('-points')[:10]
    context = {
        'matches_data': matches_data,
        'leaderboard': leaderboard,
    }
    return render(request, 'betting/predictions.html', context)


@login_required
def make_prediction(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk, status='SCHEDULED')
    existing = Prediction.objects.filter(user=request.user, match=match).first()

    if request.method == 'POST':
        form = PredictionForm(request.POST, instance=existing)
        if form.is_valid():
            pred = form.save(commit=False)
            pred.user = request.user
            pred.match = match
            # Simple odds calculation
            pred.odds = _calculate_odds(pred.prediction, match)
            pred.save()
            board, _ = PredictionLeaderboard.objects.get_or_create(user=request.user)
            board.update()
            messages.success(request, 'Pronostic enregistré !')
            return redirect('predictions')
    else:
        form = PredictionForm(instance=existing)

    return render(request, 'betting/prediction_form.html', {
        'form': form,
        'match': match,
        'existing': existing,
    })


@login_required
def my_predictions(request):
    preds = Prediction.objects.filter(user=request.user).select_related('match').order_by('-created_at')
    correct = preds.filter(is_correct=True).count()
    total = preds.exclude(is_correct=None).count()
    rate = round((correct / total * 100), 1) if total > 0 else 0
    return render(request, 'betting/my_predictions.html', {
        'predictions': preds,
        'correct': correct,
        'total': total,
        'rate': rate,
    })


def _calculate_odds(prediction, match):
    base = {
        '1': 1.80, 'X': 3.20, '2': 2.10,
        '1X': 1.30, 'X2': 1.45, '12': 1.25,
    }
    return base.get(prediction, 1.50)
