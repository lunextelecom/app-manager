'''
Created on Aug 11, 2014

@author: Duc Le
'''
DATABASES = {
    'default': {
        'NAME': 'appmanager',
        'ENGINE': 'mysql',
        'USER': 'lunexuser',
        'PASSWORD': 'n0bug4ver',
        'HOST': '10.9.9.61',  
        'SUPPORTS_TRANSACTIONS': True,
    } 
}
PREFIX_NAME = 'APP_MANAGER_'
SMS_URL = 'http://192.168.93.160:8081/sms/'
SMS_TO = '84988608168'
'''
Email setting
'''
EMAIL_HOST = "smtp2.lunextelecom.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "tcard"
EMAIL_HOST_PASSWORD = "tech88trex"

import os;
TEMPLATE_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates/')
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    TEMPLATE_ROOT
)