#!/usr/bin/python

'''
Created on Aug 18, 2014

@author: DuyNguyen
'''
import djangoenv
import gc
import logging
import requests
import sys
import statsd
import simplejson as json
import time
from django.conf import settings
from django.template import Context
from django.template.loader import get_template

from lunex.appmanagersvc.common import emailutils, httputils
from lunex.appmanagersvc.utils.daemon import Daemon
from lunex.appmanagersvc.models import Application, Configuration


settings.LOGGING_OUTPUT = "/tmp/HealthCheck_daemon.log"

logger = logging.getLogger('lunex.appmanagersvc.health_check_daemon')

import os
basedir = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig(basedir + "/logging.conf", defaults=None, disable_existing_loggers=True)

statsd_connection = statsd.Connection(host=str(settings.GRAPHITE_SERVER))
statsd_client = statsd.Client(settings.GRAPHITE_PREFIX_NAME, statsd_connection)
gauge = statsd_client.get_client(class_=statsd.Gauge)

def main(args):
    
    if len(sys.argv) == 2:
        daemon = health_check_daemon('/var/run/health-check-processor-daemon.pid')        
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1] or 'reload' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        logger.warning("No params passed, running in console mode");
        _run_service();
    return 0;

class health_check_daemon(Daemon):
    def run(self):
        try:
            _run_service()
        except Exception as inst:
            logger.exception(inst);
            raise;
        
def _run_service():
    logger.info('health_check_daemon started');   
    while True:
        try:
            process_health_check()
            gc.collect();
        except Exception as inst:
            logger.exception(inst)
        logger.info('Idle in %s seconds' % settings.SLEEPING_TIME)
        time.sleep(settings.SLEEPING_TIME);
    logger.info('health_check_daemon stopped');

def send_mail(instanceName):
    result = {'Code': 1, 'Message': 'OK'}
    try:
        template = get_template('emails/instance_down.html')
        from_email = settings.FROM_EMAIL
        to_emails = settings.TO_EMAILS
        cc = []
        subject = 'Instance may go down'
        contents = template.render(Context({'instanceName': instanceName}))
        
        server = emailutils.connect_to_server(settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        emailutils.send_email_cc_html(from_email, to_emails, subject, contents, server, cc)
        logger.debug('Instance {0} may go down, send email to '.format(instanceName, str(to_emails)))
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result

def send_sms(instanceName):
    result = {'Code': 1, 'Message': 'OK'}
    try:
        msg = "Instance {0} may go down. Please verify asap".format(instanceName)
        data = """<Data xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
            <Message>{0}</Message>
            </Data>
        """.format(msg)
        sms_tos = settings.TO_PHONES
        for item in sms_tos:
            httputils.send_request('POST', settings.SMS_URL + 'type/custom/lang/en/?srcnum={0}&dstnum={1}'.format(settings.SMS_FROM_PHONE, item), data)
            logger.debug('Send sms to ' + item + ', Content :' + msg)
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result

def process_health_check():
    try:
        apps = Application.objects.filter(Parent__isnull=False)
        for item in apps:
            try:
                conf = None
                if Configuration.objects.filter(Application=item).exists() :
                    conf = Configuration.objects.filter(Application=item)[0]
                if conf and conf.HealthUrl:
                    r = requests.get(conf.HealthUrl,timeout=5)
                    isOk = False
                    if r and r.status_code == 200:
                        isOk = True
                        #check dropwizard
                        try:
                            obj = json.loads(r.content)
                            for item in obj.items():
                                child = item[1]
                                if not child.get("healthy"):
                                    isOk = False
                                    break
                            
                        except Exception, ex:
                            pass
                    if isOk:
                        gauge.send(item.Instance, 1)
                    else:
                        gauge.send(item.Instance, 0)
                        #app goes down, send sms & email
                        send_mail(item.Instance)
                        send_sms(item.Instance)
            except:
                pass
    except Exception, ex:
        logger.exception(ex)

if __name__ == "__main__":    
    try:
        main(sys.argv)
    except Exception as inst:
        logger.exception(inst)