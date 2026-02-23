# ──────────────────────────────────────────────────────────────
# JeyaRamaDesk — Settings Package
# Automatically selects the right settings module based on
# the DJANGO_ENV environment variable.
#   - "production"  → settings.production
#   - anything else → settings.local  (default)
# ──────────────────────────────────────────────────────────────

import os

env = os.environ.get('DJANGO_ENV', 'local').lower()

if env == 'production':
    from .production import *      # noqa: F401,F403
else:
    from .local import *           # noqa: F401,F403
