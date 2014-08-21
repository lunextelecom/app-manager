'''
Created on Aug 11, 2014

@author: Duc Le
'''
#!/usr/bin/python
import sys, os;
#Setting up environment
basedir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)));
real_path = os.path.normpath(os.path.join(basedir,'../../'))

#sys.path.append(os.path.abspath(real_path))

os.environ['DJANGO_SETTINGS_MODULE'] = 'lunex.appmanagersvc.settings'

import logging.config
logging.config.fileConfig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logging.conf'))