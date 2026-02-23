import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jeyaramadesk.settings')
django.setup()

from tickets.models import Ticket
from sla.models import SLAPolicy
from django.utils import timezone

now = timezone.now()
print(f"Current time: {now}")
print()

# Check all open tickets
for t in Ticket.objects.filter(status__in=['open', 'in_progress', 'pending']):
    print(f"{t.ticket_id} | priority={t.priority} | sla_policy={t.sla_policy}")
    print(f"  response_deadline={t.sla_response_deadline}")
    print(f"  resolution_deadline={t.sla_resolution_deadline}")
    print(f"  first_response_at={t.first_response_at}")
    if t.sla_response_deadline:
        print(f"  Response deadline passed? {now > t.sla_response_deadline}")
    if t.sla_resolution_deadline:
        print(f"  Resolution deadline passed? {now > t.sla_resolution_deadline}")
    
    # Apply SLA if missing
    if not t.sla_policy:
        policy = SLAPolicy.objects.filter(priority=t.priority, is_active=True).first()
        if policy:
            t.sla_policy = policy
            t.sla_response_deadline = t.created_at + timezone.timedelta(hours=policy.response_time_hours)
            t.sla_resolution_deadline = t.created_at + timezone.timedelta(hours=policy.resolution_time_hours)
            t.save(update_fields=['sla_policy', 'sla_response_deadline', 'sla_resolution_deadline'])
            print(f"  >> Applied {policy.name} retroactively!")
    print()

# Check breaches
from sla.models import SLABreach
breaches = SLABreach.objects.all()
print(f"Total SLA breaches recorded: {breaches.count()}")
for b in breaches:
    print(f"  {b.ticket.ticket_id} - {b.breach_type} at {b.breached_at}")
