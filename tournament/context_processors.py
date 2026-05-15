from django.utils import timezone

from .models import Tournament


def active_tournament(request):
    today = timezone.localdate()
    active = Tournament.objects.filter(is_active=True)

    tournament = active.filter(
        start_date__isnull=False,
        end_date__isnull=False,
        start_date__lte=today,
        end_date__gte=today,
    ).order_by('start_date').first()

    if tournament is None:
        tournament = active.filter(
            start_date__isnull=False,
            start_date__gte=today,
        ).order_by('start_date').first()

    if tournament is None:
        tournament = active.order_by('-start_date', '-id').first()

    return {'tournament': tournament}
