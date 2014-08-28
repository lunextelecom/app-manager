#!/usr/bin/python

'''
Created on Aug 18, 2014

@author: DuyNguyen
'''
import gc
import logging
import os
import sys
import time
import djangoenv
import requests
import statsd
import simplejson as json
import socket
from django.conf import settings
from django.db import transaction
from django.template import Context
from django.template.loader import get_template
from datetime import datetime
from lunex.appmanagersvc.common import emailutils, httputils
from lunex.appmanagersvc.models import Application, Configuration, Health, \
    HealthStatus, HealthType
from lunex.appmanagersvc.utils.daemon import Daemon
from lunex.appmanagersvc.utils import Utils


settings.LOGGING_OUTPUT = "/tmp/HealthCheck_daemon.log"

basedir = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig(basedir + "/logging.conf", defaults=None, disable_existing_loggers=True)

logger = logging.getLogger('lunex.appmanagersvc.health_check_daemon')

statsd_connection = statsd.Connection(host=str(settings.GRAPHITE_SERVER))
statsd_client = statsd.Client(settings.GRAPHITE_PREFIX_NAME, statsd_connection)

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
        sms_tos = settings.SMS_TO_PHONES
        for item in sms_tos:
            httputils.send_request('POST', settings.SMS_URL + 'type/custom/lang/en/?srcnum={0}&dstnum={1}'.format(settings.SMS_FROM_PHONE, item), data)
            logger.debug('Send sms to ' + item + ', Content :' + msg)
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result

@transaction.commit_manually
def process_health_check():
    process_link_check()
    process_ping_check()
    transaction.commit()

def process_link_check():
    try:
        logger.info("begin process_health_check")
        apps = Application.objects.filter(Parent__isnull=False)
        for item in apps:
            logger.info("process_health_check %s " % item.Instance)
            try:
                conf = None
                if Configuration.objects.filter(Application=item).exists() :
                    conf = Configuration.objects.filter(Application=item)[0]
                if conf and conf.HealthUrl:
                    r = None
                    startTime = time.time()*1000
                    timer = statsd_client.get_client(class_=statsd.Timer)
                    timer.start()
                    try:
                        r = requests.get(conf.HealthUrl,timeout=5)
                    except:
                        pass
                    timer.stop(Utils.remove_special_char(item.Instance) + "." + settings.GRAPHITE_SUFFIX_RESPONSE)
                    responseTime = time.time()*1000 - startTime
                    isOk = False
                    if r and r.status_code == 200:
                        isOk = True
                        #check dropwizard
                        try:
                            obj = json.loads(r.content)
                            for child in obj.items():
                                attr = child[1]
                                if not attr.get("healthy"):
                                    isOk = False
                                    break
                            
                        except Exception, ex:
                            pass
                    healthObj = Health(Application=item,Function=conf.HealthUrl, Type=HealthType.LINK)
                    oldStatus = None
                    if Health.objects.filter(Application=item,Function=conf.HealthUrl,Type=HealthType.LINK).exists() :
                        healthObj = Health.objects.filter(Application=item,Type=HealthType.LINK)[0]
                        oldStatus = healthObj.Status
                    healthObj.LastPoll = datetime.now()
                    if isOk:
                        logger.info("process_health_check %s is OK" % item.Instance)
                        healthObj.Status = HealthStatus.GREEN
                        healthObj.LastResponseTime = responseTime
                        if str(conf.Latency) and conf.Latency*1000 <= responseTime:
                            healthObj.Status = HealthStatus.YELLOW
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.RED):
                            healthObj.LastUptime = datetime.now()
                        
                    else:
                        logger.info("process_health_check %s is not OK" % item.Instance)
                        #app goes down
                        healthObj.Status = HealthStatus.RED
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.GREEN):
                            healthObj.LastDowntime = datetime.now()
#                             send_mail(item.Instance)
#                             send_sms(item.Instance)
                    healthObj.save()
                else:
                    logger.info("conf/conf.HealthUrl of %s is null" % item.Instance)
            except Exception, ex:
                logger.info("process_health_check %s error, message : %s" % (item.Instance,ex.__str__()))
                pass
    except Exception, ex:
        logger.exception(ex)
    logger.info("end process_health_check")
    
def process_ping_check():
    try:
        logger.info("begin process_ping_check")
        apps = Application.objects.filter(Parent__isnull=False)
        for item in apps:
            logger.info("process_ping_check %s " % item.Instance)
            try:
                conf = None
                if Configuration.objects.filter(Application=item).exists() :
                    conf = Configuration.objects.filter(Application=item)[0]
                if conf and conf.Ip:
                    host = conf.Ip.split(":")[0]
                    port = int(conf.Ip.split(":")[1])
                    isOk = False
                    startTime = time.time()*1000
                    timer = statsd_client.get_client(class_=statsd.Timer)
                    timer.start()
                    try:
                        isOk = telnet(host, port)
                    except:
                        pass
                    timer.stop(Utils.remove_special_char(item.Instance) + "." + settings.GRAPHITE_SUFFIX_PING)
                    responseTime = time.time()*1000 - startTime
                  
                    healthObj = Health(Application=item,Function=conf.Ip, Type=HealthType.TELNET)
                    oldStatus = None
                    if Health.objects.filter(Application=item, Function=conf.Ip,Type=HealthType.TELNET).exists() :
                        healthObj = Health.objects.filter(Application=item,Type=HealthType.TELNET)[0]
                        oldStatus = healthObj.Status
                    healthObj.LastPoll = datetime.now()
                    if isOk:
                        logger.info("process_ping_check %s is OK" % item.Instance)
                        healthObj.Status = HealthStatus.GREEN
                        healthObj.LastResponseTime = responseTime
                        if str(conf.Latency) and conf.Latency*1000 <= responseTime:
                            healthObj.Status = HealthStatus.YELLOW
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.RED):
                            healthObj.LastUptime = datetime.now()
                        
                    else:
                        logger.info("process_ping_check %s is not OK" % item.Instance)
                        #app goes down
                        healthObj.Status = HealthStatus.RED
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.GREEN):
                            healthObj.LastDowntime = datetime.now()
#                             send_mail(item.Instance)
#                             send_sms(item.Instance)
                    healthObj.save()
                else:
                    logger.info("conf/conf.ip of %s is null" % item.Instance)
            except Exception, ex:
                logger.info("process_ping_check %s error, message : %s" % (item.Instance,ex.__str__()))
                pass
    except Exception, ex:
        logger.exception(ex)
    logger.info("end process_ping_check")
    
def telnet(host, port):
    host_addr = ""

    try:
        host_addr = socket.gethostbyname(host)

        if not host_addr:
            return False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((host, port))
        s.close()
    except:
        return False

    return True
if __name__ == "__main__":    
    try:
        process_health_check()
#         main(sys.argv)
        
    except Exception as inst:
        logger.exception(inst)
