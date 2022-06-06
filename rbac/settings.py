"""
@file_intro:
@creation_date:
@update_date:
@author:Yaqi Meng
"""
# coding=UTF-8
from __future__ import unicode_literals

from django.conf import settings

SYSTEM_GROUP_IMPLEMENTERS = getattr(settings, 'SYSTEM_GROUP_IMPLEMENTERS', [])
