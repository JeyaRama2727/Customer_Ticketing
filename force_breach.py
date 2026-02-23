"""Force SLA breach for testing — sets response deadline to the past."""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jeyaramadesk.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from tickets.models import Ticket

# Set response deadline to 1 hour ago for all open tickets without a first response
tickets = Ticket.objects.filter(
    status__in=['open', 'in_progress', 'pending'],
    sla_policy__isnull=False,
    first_response_at__isnull=True,
)

now = timezone.now()
past = now - timedelta(hours=1)

for t in tickets:
    t.sla_response_deadline = past
    t.sla_resolution_deadline = past
    t.save(update_fields=['sla_response_deadline', 'sla_resolution_deadline'])
    print(f"  {t.ticket_id} — deadlines set to {past} (1 hour ago)")

print(f"\nDone. {tickets.count()} ticket(s) will breach on next Celery beat cycle (within 5 min).")
print("Or run manually: python -c \"import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','jeyaramadesk.settings');django.setup();from sla.services.sla_service import SLAService;print(SLAService.check_all_breaches(),'breaches found')\"")
