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
        'PASSWORD': '',
        'HOST': 'localhost',
        'SUPPORTS_TRANSACTIONS': True,
    },
#     'ats_server': {
#         'NAME': 'ats',
#         'ENGINE': 'mysql',
#         'USER': 'lunexuser',
#         'PASSWORD': 'inn0v@tion',
#         'HOST': '10.9.9.61',
#         'SUPPORTS_TRANSACTIONS': True,
#     },
}

INSTALLED_APPS = (
    'lunex.appmanagersvc'
)

LOGGING_OUTPUT = 'STDOUT'
LOGGING_LEVEL = 'DEBUG'

from prod_settings import *
