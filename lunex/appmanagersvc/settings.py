'''
Created on Aug 11, 2014

@author: Duc Le
'''
import os
basedir = os.path.dirname(os.path.abspath(__file__))

DEBUG = True

DATABASES = {
    'default': {
        'NAME': 'appmanager',
        'ENGINE': 'mysql',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'SUPPORTS_TRANSACTIONS': True,
    }
}

INSTALLED_APPS = (
    'lunex.appmanagersvc'
)

LOGGING_OUTPUT = 'STDOUT'
LOGGING_LEVEL = 'DEBUG'
SLEEPING_TIME = 60
SMS_URL = 'http://192.168.93.160:8081/sms/'
SMS_FROM_PHONE = '6782718212'
SMS_TO_PHONES = ['84988608168']
'''
Email setting
'''
EMAIL_HOST = "smtp2.lunextelecom.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "tcard"
EMAIL_HOST_PASSWORD = "tech88trex"
FROM_EMAIL = ['devteam@lunextelecom.com']
TO_EMAILS = ['duynguyen@lunextelecom.com']

'''Template dir'''
import os;
TEMPLATE_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates/')
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    TEMPLATE_ROOT
)
'''Graphite'''
GRAPHITE_PREFIX_NAME = 'test.app_manager'
GRAPHITE_SERVER = "192.168.93.112"
GRAPHITE_OUTPUT_PORT = 8001
GRAPHITE_SUFFIX_RESPONSE = 'reponse_time'
GRAPHITE_SUFFIX_PING = 'ping_time'
from lunex.appmanagersvc.prod_settings import *
