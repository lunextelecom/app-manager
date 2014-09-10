#!/usr/bin/python

'''
Created on Aug 18, 2014

@author: DuyNguyen
'''
import gc
import logging
import os
import socket
import sys
import time
import djangoenv
import requests
import statsd
import simplejson as json

from datetime import datetime, timedelta
from string import lower
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.template import Context
from django.template.loader import get_template

from lunex.appmanagersvc.common import emailutils, httputils
from lunex.appmanagersvc.models import Application, Health, \
    HealthStatus, HealthType, HealthConf
from lunex.appmanagersvc.utils import Utils
from lunex.appmanagersvc.utils.daemon import Daemon


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

def process_health_check():
    logger.debug("start process_health_check")
    try:
        process_link_check()
    except Exception, ex:
        logger.exception(ex)
    try:
        process_ping_check()
    except Exception, ex:
        logger.exception(ex)
    logger.debug("end process_health_check")

def get_full_url(ip, url):
    """
    Returns true if s is valid http url, else false 
    Arguments:
    - `s`:
    """
    ip = ip if ip else ''
    if url.startswith('http'):
        return url
    else:
        return ip + url
    
def _check_url_alive(metricName, url):
    r = None
    startTime = time.time()*1000
    timer = statsd_client.get_client(class_=statsd.Timer)
    timer.start()
    try:
        r = requests.get(url,timeout=5)
    except:
        pass
    timer.stop(metricName)
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
    return isOk, responseTime

@transaction.commit_manually
def process_link_check():
    try:
        logger.debug("begin process_link_check")
        apps = Application.objects.filter(Parent__isnull=False)
        map_graphite = {}
        is_get_graphite = False
        for item in apps:
            logger.debug("process_link_check %s " % item.Instance)
            try:
                latency = None
                if item.Latency:
                    latency = item.Latency
                elif item.Parent.Latency:
                    latency = item.Parent.Latency
                
                lstHealthCheck = None 
                if HealthConf.objects.filter((Q(Application=item)|Q(Application=item.Parent))).exists() :
                    lstHealthCheck = HealthConf.objects.filter((Q(Application=item)|Q(Application=item.Parent)))
                if lstHealthCheck :
                    for child in lstHealthCheck:
                        metricName = Utils.remove_special_char(item.Instance + '@' + child.Name);
                        url = child.Url
                        url = get_full_url(item.Ip, url)
                        isOk, responseTime = _check_url_alive(metricName, url)
                        healthObj = Health(Application=item, Function=url, MetricName=metricName, Type=HealthType.LINK)
                        oldStatus = None
                        if Health.objects.filter(Application=item, Function=url, MetricName=metricName, Type=HealthType.LINK).exists() :
                            healthObj = Health.objects.filter(Application=item, Function=url, MetricName=metricName, Type=HealthType.LINK)[0]
                            oldStatus = healthObj.Status
                        healthObj.LastPoll = datetime.now()
                        if isOk:
                            logger.debug("process_link_check %s is OK" % item.Instance)
                            healthObj.Status = HealthStatus.GREEN
                            healthObj.LastResponseTime = responseTime
                            if str(latency) and latency*1000 <= responseTime:
                                healthObj.Status = HealthStatus.YELLOW
                            if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.RED):
                                healthObj.LastUptime = datetime.now()
                           
                            if (healthObj.Last1HrTime and (healthObj.Last1HrTime + timedelta(minutes=1)) <= datetime.now()) or not healthObj.Last1HrTime:
                                healthObj.Last1HrTime = datetime.now()
                                lstValue = []
                                if healthObj.Last24HrValue:
                                    lstValue = json.loads(healthObj.Last24HrValue)
                                if lstValue and len(lstValue) >= 24:
                                    lstValue.pop(0)
                                if not is_get_graphite:
                                    is_get_graphite = True
                                    map_graphite = get_avg_response_time(1)
                                if map_graphite and map_graphite.has_key(metricName):
                                    lstValue.append(map_graphite.get(metricName))
                                healthObj.Last24HrValue = json.dumps(lstValue)
                        else:
                            logger.debug("process_link_check %s is not OK" % item.Instance)
                            #app goes down
                            healthObj.Status = HealthStatus.RED
                            if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.GREEN):
                                healthObj.LastDowntime = datetime.now()
                                send_mail(item.Instance)
                                send_sms(item.Instance)
                        healthObj.save()
                
            except Exception, ex:
                logger.debug("process_link_check %s error, message : %s" % (item.Instance,ex.__str__()))
                pass
    except Exception, ex:
        logger.exception(ex)
    logger.debug("end process_link_check")
    transaction.commit()

@transaction.commit_manually    
def process_ping_check():
    try:
        logger.debug("begin process_ping_check")
        apps = Application.objects.filter(Parent__isnull=False)
        map_graphite = {}
        is_get_graphite = False
        for item in apps:
            logger.debug("process_ping_check %s " % item.Instance)
            try:
                if item.Ip:
                    metricName = Utils.remove_special_char(item.Instance + '@ping');
                    latency = None
                    if item.Latency:
                        latency = item.Latency
                    elif item.Parent.Latency:
                        latency = item.Parent.Latency
                    ip = item.Ip
                    ip = ip.lower().replace("http://","").replace("https://","")
                    host = ip.split(":")[0]
                    port = int(ip.split(":")[1])
                    isOk = False
                    startTime = time.time()*1000
                    timer = statsd_client.get_client(class_=statsd.Timer)
                    timer.start()
                    try:
                        isOk = telnet(host, port)
                    except:
                        pass
                    timer.stop(metricName)
                    responseTime = time.time()*1000 - startTime
                  
                    healthObj = Health(Application=item,Function=item.Ip, MetricName=metricName, Type=HealthType.TELNET)
                    oldStatus = None
                    if Health.objects.filter(Application=item, Function=item.Ip, MetricName=metricName, Type=HealthType.TELNET).exists() :
                        healthObj = Health.objects.filter(Application=item, Function=item.Ip, MetricName=metricName, Type=HealthType.TELNET)[0]
                        oldStatus = healthObj.Status
                    healthObj.LastPoll = datetime.now()
                    if isOk:
                        logger.info("process_ping_check %s is OK" % item.Instance)
                        healthObj.Status = HealthStatus.GREEN
                        healthObj.LastResponseTime = responseTime
                        if str(latency) and latency*1000 <= responseTime:
                            healthObj.Status = HealthStatus.YELLOW
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.RED):
                            healthObj.LastUptime = datetime.now()
                        
                        if (healthObj.Last1HrTime and (healthObj.Last1HrTime + timedelta(hours=1)) <= datetime.now()) or not healthObj.Last1HrTime:
                            healthObj.Last1HrTime = datetime.now()
                            lstValue = []
                            if healthObj.Last24HrValue:
                                lstValue = json.loads(healthObj.Last24HrValue)
                            if lstValue and len(lstValue) > 0:
                                lstValue.pop()
                            if not is_get_graphite:
                                is_get_graphite = True
                                map_graphite = get_avg_response_time(1)
                            if map_graphite and map_graphite.has_key(metricName):
                                lstValue.append(map_graphite.get(metricName))
                            healthObj.Last24HrValue = json.dumps(lstValue)
                        
                    else:
                        logger.debug("process_ping_check %s is not OK" % item.Instance)
                        #app goes down
                        healthObj.Status = HealthStatus.RED
                        if (not oldStatus) or (oldStatus and oldStatus==HealthStatus.GREEN):
                            healthObj.LastDowntime = datetime.now()
                            send_mail(item.Instance)
                            send_sms(item.Instance)
                    healthObj.save()
                else:
                    logger.debug("conf/conf.ip of %s is null" % item.Instance)
            except Exception, ex:
                logger.debug("process_ping_check %s error, message : %s" % (item.Instance,ex.__str__()))
                pass
    except Exception, ex:
        logger.exception(ex)
    logger.debug("end process_ping_check")
    transaction.commit()
    
def get_avg_response_time(numHours):
    map = {}
    rawData = None
    try:
        url = "http://{0}:{1}/render/?target={2}.*.*.*.sum&maxDataPoints=1&format=json&from=-{3}h".format(settings.GRAPHITE_SERVER, settings.GRAPHITE_OUTPUT_PORT, settings.GRAPHITE_PREFIX_NAME, numHours)
        rawData = requests.get(url ,timeout=5)
        logger.info('graphite get avg response time : ' + url)
    except Exception, ex:
        pass
    if rawData:
        try:
            obj = json.loads(rawData.content)
            for child in obj:
                target = child.get("target")
                target = lower(child.get("target").replace(settings.GRAPHITE_PREFIX_NAME +'.','').replace('.sum','')).strip()
                datapoints = int(child.get("datapoints")[0][0])
                map[target] = datapoints
        except Exception, ex:
            pass
    return map

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
        main(sys.argv)
    except Exception as inst:
        logger.exception(inst)
