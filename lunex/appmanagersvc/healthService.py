'''
Created on Aug 18, 2014

@author: Duy nguyen
'''
from email import MIMEMultipart, MIMEText, MIMEImage, MIMEBase
import logging

from django.conf import settings
from django.template import Context
from django.template.loader import get_template
import requests
import statsd

from lunex.appmanagersvc.models import Application, Configuration
from lunex.appmanagersvc.common import emailutils


logger = logging.getLogger('lunex.appmanagersvc.health_service')
def health_service():
    result = {'Code': 1, 'Message': 'OK'}
    try:
        apps = Application.objects.filter(Parent__isnull=False)
        for item in apps:
            conf = None
            if Configuration.objects.filter(Application=item).exists() :
                conf = Configuration.objects.filter(Application=item)[0]
            if conf and conf.HealthUrl:
                r = requests.get(conf.HealthUrl,timeout=5)
                if r and r.status_code == 200:
                    gauge = statsd.Gauge(settings.PREFIX_NAME + item.Instance)
                    gauge.send('status', 1)
                else:
                    
                    #app goes down, send sms & email
                    pass
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result

def send_mail(instanceName):
    result = {'Code': 1, 'Message': 'OK'}
    try:
        template = get_template('emails/instance_down.txt')
        from_email = ['devteam@lunextelecom.com']
        email_tos = ['duynguyen@lunextelecom.com']
        cc = []
        subject = 'Instance goes down'
        contents = template.render(Context({'instanceName': instanceName}))
        
        server = emailutils.connect_to_server(settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        emailutils.send_email_cc_html(from_email, email_tos, subject, contents, server, cc)
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result
