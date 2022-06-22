from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    today = datetime.today().year
    return {
        'year': today,
    }
