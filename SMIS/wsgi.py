"""
WSGI config for SMIS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""


import os,sys
sys.path.append("/home/virtualenv/django/lib/python3.7/site-packages")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "SMIS.settings")
sys.path.append('/var/www/html/safe')

application = get_wsgi_application()
