"""
WSGI config for inflaskart project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
# for deployment on Heroku
from whitenoise.django import DjangoWhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inflaskart.settings")

application = get_wsgi_application()
# for deployment on Heroku
application = DjangoWhiteNoise(application)
