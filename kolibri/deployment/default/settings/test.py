from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import tempfile

# If KOLIBRI_HOME isn't defined in the test env, it's okay to just set a
# temp directory for testing.
if "KOLIBRI_HOME" not in os.environ:
    os.environ["KOLIBRI_HOME"] = tempfile.mkdtemp()


from .base import *  # noqa isort:skip @UnusedWildImport

try:
    process_cache = CACHES["process_cache"]  # noqa F405
except KeyError:
    process_cache = None

# Create a dummy cache for each cache
CACHES = {
    key: {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
    for key in CACHES  # noqa F405
}

if process_cache:
    CACHES["process_cache"] = process_cache

TESTING = True

# The edulution plugin's LSHE grade bands are enforced by default (a class
# with no band can receive no assignments). Core lesson/quiz tests create
# classes without bands, so tests run with enforcement off; the grade band
# tests turn it on explicitly.
LSHE_GRADE_BANDS = "off"
