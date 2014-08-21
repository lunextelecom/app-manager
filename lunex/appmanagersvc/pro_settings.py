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
SLEEPING_TIME = 60
SMS_URL = 'http://192.168.93.160:8081/sms/'
'''
Email setting
'''
EMAIL_HOST = "smtp2.lunextelecom.com"
EMAIL_PORT = 25
EMAIL_HOST_USER = "tcard"
EMAIL_HOST_PASSWORD = "tech88trex"
FROM_EMAIL = 'trinhtran@lunextelecom.com'
TO_EMAILS = 'duynguyen@lunextelecom.com'
TO_PHONES = '84988608168'

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
GRAPHITE_PREFIX_NAME = 'APP_MANAGER_'
GRAPHITE_SERVER = "192.168.93.69"
GRAPHITE_PORT = 8001