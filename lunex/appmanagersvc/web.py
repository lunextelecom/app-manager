'''
Created on Aug 11, 2014

@author: Duc Le
'''
import bottle
import logging
import os
import time
import djangoenv
import requests
import simplejson as json

from bottle import request, static_file
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from gevent.pywsgi import WSGIServer
from lunex.appmanagersvc.common import httputils
from lunex.appmanagersvc.models import Application, Configuration, Health, HealthType
from string import upper
from time import mktime
from lunex.appmanagersvc.utils import Utils

app = bottle.Bottle()


basedir = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig(basedir + "/logging.conf", defaults=None, disable_existing_loggers=True)
logger = logging.getLogger('lunex.appmanagersvc.web')

basedir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)));
#doc_path = os.path.normpath(os.path.join(basedir,'../../doc/build/html'))
static_path = os.path.normpath(os.path.join(basedir,'../../data/static'))
bottle.TEMPLATE_PATH = [static_path,]

success_code = 1
error_code = -1
map_ext_dict = {'application/json': 'json',
                'application/xml': 'xml',
                'application/yaml': 'yaml',
                'application/text': 'txt',
                'application/python': 'py'
                }

@app.route('/', name='default')
def index():
    logger.debug('It works')
    return {'Message': 'AppManagerSVC - It works'}

@app.route('/config', method='GET', name='get_config')
@app.route('/config/', method='GET', name='get_config')
def get_config():
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        isGetFromApp = params.get('get_from_app')
        if not isGetFromApp:
            isGetFromApp = False
        assert instance, 'Instance is invalid'
        code = success_code
        message = 'OK'
        appName = None
        try :
            appName = instance.split("@")[0]
        except Exception:
            assert instance, 'instance param is invalid'
        parent_obj = Application.objects.filter(AppName=appName)
        if parent_obj :
            parent_obj = parent_obj[0]
        else:
            raise Exception('App [%s] does not exist' % appName)
        try:
            app_obj = Application.objects.get(Instance=instance)
        except Application.DoesNotExist:
            raise Exception('Instance [%s] does not exist' % instance)
        
        if Configuration.objects.filter(Application=app_obj).exists():
            config_obj = Configuration.objects.get(Application=app_obj)
        
        if isGetFromApp and ((config_obj and config_obj.Content) or not config_obj):
            if not Configuration.objects.filter(Application=parent_obj).exists():
                code = error_code
                message = 'config does not exist'
            else:
                config_obj = Configuration.objects.get(Application=parent_obj)
        if not config_obj:
            code = error_code
            message = 'config does not exist'
            
        if code != -1:
            content = config_obj.Content
            mime_type = config_obj.MimeType
            if mime_type not in map_ext_dict:
                raise Exception('MimeType [%s] is invalid' % mime_type)
            ext = map_ext_dict[mime_type]
            name = static_path + '/' + config_obj.Filename
#             file_name = '%s.%s' % (name, ext)
            file_name = name
            afile = open(file_name, 'w')
            afile.write(content)
            afile.close()
            return static_file(filename=config_obj.Filename, root=static_path, download=config_obj.Filename)
    
    except Exception, ex:
        logger.exception(ex)
        code = error_code
        message = ex.__str__()
    return {'Code': code, 'Message':message}

  
@app.route('/config', method='PUT', name='save_config')
@app.route('/config/', method='PUT', name='save_config')
def save_config():
    try:
        params = dict(request.query.items())
        try:
            paramsPost = dict(request.json) 
            params.update(paramsPost)
        except:
            pass
        config_url = params.get('config_url', '')
        health_url = params.get('health_url', '')
        mime_type = params.get('mime_type', '')
        filename = params.get('filename', '')
        content = params.get('content', '')
        updatedby = params.get('updatedby', '').strip()
        latency = params.get('latency', '')
        ip = params.get('ip', '')
        assert updatedby, 'updatedby param can not null'
        code = success_code
        message = 'OK'
        apps = Application.objects.filter()
        appId = params.get('id', '').strip()
        if appId:
            apps = apps.filter(pk=appId)
        else:
            code = error_code
            message = 'id does not exist'
        if code != -1:
            for app_obj in apps:
                conf = Configuration(Application=app_obj,CreatedBy=updatedby)
                oldContent = None
                if Configuration.objects.filter(Application=app_obj).exists() :
                    conf = Configuration.objects.filter(Application=app_obj)[0]
                    oldContent = conf.Content
                if config_url:
                    conf.ConfigUrl = config_url
                if health_url:
                    conf.HealthUrl = health_url
                if mime_type:
                    conf.MimeType = mime_type
                if latency:
                    conf.Latency = latency
                if ip:
                    conf.Ip = ip
                conf.Content = content
                if filename:
                    conf.Filename = filename
                conf.UpdatedBy = updatedby
                conf.save()
                app_obj.UpdatedBy = updatedby
                app_obj.save()
                #put config change
                if config_url:
                    if content:
                        if oldContent and content != oldContent:
                            update_config_fly(app_obj.Instance, config_url, filename, content)
                    elif oldContent and app_obj.Parent:
                        #get config from parent
                        if Configuration.objects.filter(Application=app_obj.Parent).exists():
                            parent_conf = Configuration.objects.get(Application=app_obj.Parent)
                            if parent_conf.content:
                                update_config_fly(app_obj.Instance, config_url, parent_conf.filename, parent_conf.content)
                            
    except Exception, ex:
        logger.exception(ex)
        code = error_code
        message = ex.__str__()
    return {'Code': code, 'Message': message}

def update_config_fly(instanceName, url, filename, content):
    try:
        params = json.dumps({'filename': filename, 'content': content})
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        response = httputils.send_request("POST", url, params, headers)
        logger.info("update instance {0} with config {1}, status : {2}, reason : {3}".format(instanceName, content, response.status, response.reason))
    except Exception, ex:
        logger.exception(ex)
        
@app.route('/config', method='DELETE', name='delete_config')
@app.route('/config/', method='DELETE', name='delete_config')
def delete_config():
    try:
        params = dict(request.query.items())
        code = success_code
        message = 'OK'
        apps = Application.objects.filter()
        appId = params.get('id', '').strip()
        if appId:
            apps = apps.filter(pk=appId)
        else:
            code = error_code
            message = 'id does not exist'
        if code != -1:
            for app_obj in apps:
                if Configuration.objects.filter(Application=app_obj).exists() :
                    conf = Configuration.objects.filter(Application=app_obj)
                    conf.delete()
    except Exception, ex:
        logger.exception(ex)
        code = error_code 
        message = ex.__str__()
    return {'Code': code, 'Message': message}

@app.route('/app', method='POST', name='register_app')
@app.route('/app/', method='POST', name='register_app')
@transaction.commit_manually
def register_app():
    try:
        params = dict(request.query.items())
        try:
            paramsPost = dict(request.json) 
            params.update(paramsPost)
        except:
            pass
        code = success_code
        message = 'OK'
        instance = params.get('instance', '').strip()
        createdBy = params.get('createdby', '').strip()
        assert createdBy, 'createdBy param can not null'
        assert instance, 'instance param is invalid'
        appName = None;
        try :
            appName = instance.split("@")[0]
        except Exception:
            assert instance, 'instance param is invalid'
        parent_obj = Application.objects.filter(AppName=appName)
        if parent_obj :
            parent_obj = parent_obj[0]
        else:
            parent_obj = Application(AppName=appName, CreatedBy=createdBy)
            parent_obj.save()
        if not Application.objects.filter(Instance=instance).exists() :
            app_obj = Application(AppName=appName, Instance=instance, Parent=parent_obj, CreatedBy=createdBy)
            app_obj.save()
            config_url = params.get('config_url', '')
            health_url = params.get('health_url', '')
            mime_type = params.get('mime_type', '')
            filename = params.get('filename', '')
            content = params.get('content', '')
            latency = params.get('latency', '')
            ip = params.get('ip', '')
            isCreateConf = False
            conf = Configuration(Application=app_obj,CreatedBy=createdBy)
            if config_url:
                isCreateConf = True
                conf.ConfigUrl = config_url
            if health_url:
                isCreateConf = True
                conf.HealthUrl = health_url
            if mime_type:
                isCreateConf = True
                conf.MimeType = mime_type
            if content:
                isCreateConf = True
                conf.Content = content
            if filename:
                isCreateConf = True
                conf.Filename = filename
            if latency:
                isCreateConf = True
                conf.Latency = latency
            if ip:
                isCreateConf = True
                conf.Ip = ip
            if isCreateConf == True:
                conf.save()
            transaction.commit()
        else:
            code = error_code
            message = 'instance has already been created'
            transaction.rollback()
            
    except Exception, ex:
        transaction.rollback()
        logger.exception(ex)
        code = error_code
        message = ex.__str__()
    return {'Code': code, 'Message': message}

@app.route('/app', method='DELETE', name='unregister_app')
@app.route('/app/', method='DELETE', name='unregister_app')
def unregister_app():
    try:
        params = dict(request.query.items())
        try:
            paramsPost = dict(request.json) 
            params.update(paramsPost)
        except:
            pass
        code = success_code
        message = 'OK'
        apps = Application.objects.filter()
        appId = params.get('id', '').strip()
        if appId:
            apps = apps.filter(pk=appId)
        else:
            code = error_code
            message = 'id does not exist'
        if code != -1:
            for app_obj in apps:
                if app_obj.Parent:
                    children = app_obj.children.all()
                    for item in children:
                        if Configuration.objects.filter(Application=item).exists() :
                            conf = Configuration.objects.filter(Application=item)
                            conf.delete()
                        item.delete()
                
                if Configuration.objects.filter(Application=app_obj).exists() :
                    conf = Configuration.objects.filter(Application=app_obj)
                    conf.delete()
                app_obj.delete()
    except Exception, ex:
        logger.exception(ex)
        code = error_code
        message = ex.__str__()
    return {'Code': code, 'Message': message}
    
@app.route('/list', method='GET', name='list_instance')
@app.route('/list/', method='GET', name='list_instance')
def list_instance():
    result = {'Code': 1, 'Message': 'OK'}
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        apps = Application.objects.filter()
        if instance:
            apps = apps.filter(Q(Instance__icontains=instance)|Q(AppName__icontains=instance))
            
        app_list = []
        for item in apps:
            r = get_instance_detail(item)
            app_list.append(r)
            
        result['Result'] = app_list
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': error_code, 'Message': ex.__str__()}
    return result

@app.route('/app', method='GET', name='get_instance')
@app.route('/app/', method='GET', name='get_instance')
def get_instance():
    result = {'Code': 1, 'Message': 'OK'}
    try:
        params = dict(request.query.items())
        apps = Application.objects.filter()
        appId = params.get('id', '').strip()
        if appId:
            apps = apps.filter(pk=appId)
            
        app_list = []
        for item in apps:
            r = get_instance_detail(item)
            app_list.append(r)
            
        result['Result'] = app_list
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result

def get_instance_detail(instance):
    r = {}
    r['Id'] = instance.pk
    r['AppName'] = instance.AppName
    r['Instance'] = instance.Instance
    r['CreatedBy'] = instance.CreatedBy
    r['CreatedDate'] = instance.CreatedDate.strftime('%m/%d/%Y %I:%M:%S %p')
    r['UpdatedBy'] = instance.UpdatedBy if instance.UpdatedBy else None
    r['Type'] = 1 if instance.Parent else 0
    r['UpdatedDate'] = instance.UpdatedDate.strftime('%m/%d/%Y %I:%M:%S %p') if instance.UpdatedDate else None
    r['Content'] = ''
    r['Filename'] = ''
    r['ConfigUrl'] = ''
    r['HealthUrl'] = ''
    r['Latency'] = ''
    r['Ip'] = ''
    conf = None
    if Configuration.objects.filter(Application=instance).exists() :
        conf = Configuration.objects.filter(Application=instance)[0]
    if conf:
        r['Content'] = conf.Content if conf.Content else '' 
        r['Filename'] = conf.Filename if conf.Filename else '' 
        r['ConfigUrl'] = conf.ConfigUrl if conf.ConfigUrl else '' 
        r['HealthUrl'] = conf.HealthUrl if conf.HealthUrl else '' 
        r['Latency'] = conf.Latency if str(conf.Latency) else ''
        r['Ip'] = conf.Ip if conf.Ip else ''
    return r

@app.route('/health', method='GET', name='list_health')
@app.route('/health/', method='GET', name='list_health')
def list_health():
    result = {'Code': 1, 'Message': 'OK'}
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        
        lstHealth = Health.objects.filter().order_by('Application__Instance')
        if instance:
            lstHealth = lstHealth.filter(Application__Instance__icontains=instance)
#         http://192.168.93.112:8001/render/?target=test.appmanager.*.responseTime.sum&maxDataPoints=1&format=json
        
        map24Ping = get_avg_response_time(24, settings.GRAPHITE_SUFFIX_PING)
        map1Ping = get_avg_response_time(1, settings.GRAPHITE_SUFFIX_PING)
        
        map24Response = get_avg_response_time(24, settings.GRAPHITE_SUFFIX_RESPONSE)
        map1Response = get_avg_response_time(1, settings.GRAPHITE_SUFFIX_RESPONSE)
        app_list = []
        for item in lstHealth:
            r = {}
            r['Id'] = item.pk
            r['Instance'] = item.Application.Instance  
            r['Function'] = item.Function
            r['Type'] = item.Type
            r['Status'] = item.Status
            r['LastDowntime'] = item.LastDowntime.strftime('%m/%d/%Y %I:%M:%S %p') if item.LastDowntime else None
            r['LastUptime'] = item.LastUptime.strftime('%m/%d/%Y %I:%M:%S %p') if item.LastUptime else None
            r['LastPoll'] = item.LastPoll.strftime('%m/%d/%Y %I:%M:%S %p') if item.LastPoll else None
            r['LastResponseTime'] = item.LastResponseTime if item.LastResponseTime else '' 
            r['Uptime'] = (time.time() - (mktime(item.LastUptime.timetuple()) + item.LastUptime.microsecond/1000000.0))*1000 if item.LastUptime else ''
            if item.Type and item.Type == HealthType.LINK:
                r['AvgLast1Hr'] = map1Response.get(upper(Utils.remove_special_char(item.Application.Instance))) if map1Response.get(upper(Utils.remove_special_char(item.Application.Instance))) else ''
                r['AvgLast24Hr'] = map24Response.get(upper(Utils.remove_special_char(item.Application.Instance))) if map24Response.get(upper(Utils.remove_special_char(item.Application.Instance))) else ''
            else:
                r['AvgLast1Hr'] = map1Ping.get(upper(Utils.remove_special_char(item.Application.Instance))) if map1Ping.get(upper(Utils.remove_special_char(item.Application.Instance))) else ''
                r['AvgLast24Hr'] = map24Ping.get(upper(Utils.remove_special_char(item.Application.Instance))) if map24Ping.get(upper(Utils.remove_special_char(item.Application.Instance))) else ''
            app_list.append(r)
        result['Result'] = app_list
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': error_code, 'Message': ex.__str__()}
    return result

def get_avg_response_time(numHours, suffixName):
    map = {}
    rawData = None
    try:
        url = "http://{0}:{1}/render/?target={2}.*.{3}.sum&maxDataPoints=1&format=json&from=-{4}h".format(settings.GRAPHITE_SERVER, settings.GRAPHITE_OUTPUT_PORT, settings.GRAPHITE_PREFIX_NAME, suffixName, numHours)
        rawData = requests.get(url ,timeout=5)
        logger.info('graphite get avg response time : ' + url)
    except Exception, ex:
        pass
    if rawData:
        try:
            obj = json.loads(rawData.content)
            for child in obj:
                target = child.get("target")
                target = upper(child.get("target").replace(settings.GRAPHITE_PREFIX_NAME +'.','').replace('.' + suffixName+'.sum',''))
                datapoints = int(child.get("datapoints")[0][0])
                map[target] = datapoints
        except Exception, ex:
            pass
    return map
#====================================Init======================================#
def init_server():
    from django.conf import settings
    
init_server()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", help="ip address")
    parser.add_argument("-p", help="port")
    args = parser.parse_args()    
    ip_addr = '0.0.0.0'
    port = 9004
    if args.i:
        ip_addr = args.i
    if args.p:
        port = int(args.p)
    logger.info('Listening on %s:%s', ip_addr, port)
    WSGIServer((ip_addr, port), app).serve_forever()
