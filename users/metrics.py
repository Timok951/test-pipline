import os
from django.contrib.auth import get_user_model
from users.models import Role
from prometheus_client import Gauge, Counter, CollectorRegistry, multiprocess

PROM_DIR = os.path.join(os.getcwd(), 'metrics_data')
os.makedirs(PROM_DIR, exist_ok=True)
os.environ['PROMETHEUS_MULTIPROC_DIR'] = PROM_DIR

registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)

# Gauge models
total_users_gauge = Gauge('app_total_users', 'Общее количество пользователей', registry=registry, multiprocess_mode='all')
total_roles_gauge = Gauge('app_total_roles', 'Количество ролей в системе', registry=registry, multiprocess_mode='all')
avg_bonus_gauge = Gauge('app_average_bonus', 'Средний бонус пользователей', registry=registry, multiprocess_mode='all')

# Auth counter
login_counter = Counter('app_logins_total', 'Количество выполненных логинов', registry=registry)

def update_metrics():
    User = get_user_model()
    total_users_gauge.set(User.objects.count())
    total_roles_gauge.set(Role.objects.count())
    from django.db.models import Avg
    avg_bonus_gauge.set(User.objects.all().aggregate(avg=Avg('bonus'))['avg'] or 0)
