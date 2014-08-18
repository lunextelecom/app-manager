'''
Created on Aug 11, 2014

@author: Duc Le
'''
import bottle
import logging
import djangoenv
import settings
import simplejson
from bottle import route, run, error, get, post, request, response, static_file
from gevent.pywsgi import WSGIServer
#from lunex.utilities import httputils
from lunex.appmanagersvc.models import Application, Configuration
from django.db import transaction
app = bottle.Bottle()

logger = logging.getLogger('lunex.appmanagersvc.web')

import os
basedir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)));
#doc_path = os.path.normpath(os.path.join(basedir,'../../doc/build/html'))
static_path = os.path.normpath(os.path.join(basedir,'../../data/static'))
bottle.TEMPLATE_PATH = [static_path,]

map_ext_dict = {'application/json': 'json',
                'application/xml': 'xml',
                'application/yaml': 'yaml',
                'application/text': 'txt'
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
        code = 0
        message = ''
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
        if not Configuration.objects.filter(Application=app_obj).exists():
            if isGetFromApp==True:
                if not Configuration.objects.filter(Application=parent_obj).exists():
                    code = -1
                    message = 'config does not exist'
                   
                else:
                    config_obj = Configuration.objects.get(Application=parent_obj)
            else:
                code = -1
                message = 'config does not exist'
                
        else:
            config_obj = Configuration.objects.get(Application=app_obj)
        if code != -1:
            content = config_obj.Content
            mime_type = config_obj.MimeType
            if mime_type not in map_ext_dict:
                raise Exception('MimeType [%s] is invalid' % mime_type)
            ext = map_ext_dict[mime_type]
            name = static_path + '/' + instance.replace(':', '_')#datetime.now().strftime('%m_%d_%Y_%H_%m_%S')
            file_name = '%s.%s' % (name, ext)
            afile = open(file_name, 'w')
            afile.write(content)
            afile.close()
            return static_file(filename=file_name, root=static_path, download=file_name)
        else:
            return {'Code': code, 'Message':message}
    
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

  
@app.route('/config', method='PUT', name='save_config')
@app.route('/config/', method='PUT', name='save_config')
def save_config():
    try:
        paramsPost = dict(request.json) 
        params = dict(request.query.items())
        params.update(paramsPost)
        appName = params.get('app', '').strip()
        instance = params.get('instance', '').strip()
        if not appName and not instance:
            return {'Code': -1, 'Message':'app/instance param can not be null'}
        app_obj = None
        if appName :
            if not Application.objects.filter(AppName=appName).exists():
                return {'Code': -1, 'Message':'app does not exist'}
            else:
                app_obj = Application.objects.filter(AppName=appName)[0]
        else:
            if not Application.objects.filter(Instance=instance).exists():
                return {'Code': -1, 'Message':'instance does not exist'}
            else:
                app_obj = Application.objects.filter(Instance=instance)[0]
        config_url = params.get('config_url', '')
        health_url = params.get('health_url', '')
        mime_type = params.get('mime_type', '')
        filename = params.get('filename', '')
        content = params.get('content', '')
        conf = Configuration(Application=app_obj)
        if Configuration.objects.filter(Application=app_obj).exists() :
            conf = Configuration.objects.filter(Application=app_obj)[0]
            
        if config_url:
            conf.ConfigUrl = config_url
        if health_url:
            conf.HealthUrl = config_url
        if mime_type:
            conf.MimeType = mime_type
        if content:
            conf.Content = content
        if filename:
            conf.Filename = filename
        conf.save()
        return {'Code': 1}
       
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/config', method='DELETE', name='delete_config')
@app.route('/config/', method='DELETE', name='delete_config')
def delete_config():
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        assert instance, 'instance param is invalid'

        if Application.objects.filter(Instance=instance).exists() :
            app_obj = Application.objects.filter(Instance=instance)[0]
            if Configuration.objects.filter(Application=app_obj).exists() :
                conf = Configuration.objects.filter(Application=app_obj)
                conf.delete()
        return {'Code': 1}
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/app', method='POST', name='register_app')
@app.route('/app/', method='POST', name='register_app')
@transaction.commit_manually
def register_app():
    try:
        paramsPost = dict(request.json) 
        params = dict(request.query.items())
        params.update(paramsPost)
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
            isCreateConf = False
            conf = Configuration(Application=app_obj)
            if config_url:
                isCreateConf = True
                conf.ConfigUrl = config_url
            if health_url:
                isCreateConf = True
                conf.HealthUrl = config_url
            if mime_type:
                isCreateConf = True
                conf.MimeType = mime_type
            if content:
                isCreateConf = True
                conf.Content = content
            if filename:
                isCreateConf = True
                conf.Filename = filename
            if isCreateConf == True:
                conf.save()
            transaction.commit()
            return {'Code': 1}
        else:
            return {'Code': -1, 'Message': 'instance has already been created'}
    except Exception, ex:
        transaction.rollback()
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/app', method='DELETE', name='unregister_app')
@app.route('/app/', method='DELETE', name='unregister_app')
def unregister_app():
    try:
        paramsPost = dict(request.json) 
        params = dict(request.query.items())
        params.update(paramsPost)
        instance = params.get('instance', '').strip()
        assert instance, 'instance param is invalid'
        if Application.objects.filter(Instance=instance).exists() :
            app_obj = Application.objects.filter(Instance=instance)[0]
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
        return {'Code': -1, 'Message': ex.__str__()}
    
@app.route('/list', method='GET', name='list_instance')
@app.route('/list/', method='GET', name='list_instance')
def list_instance():
    result = {'Code': 1, 'Message': ''}
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        apps = Application.objects.filter()
        if instance:
            apps = apps.filter(Instance__icontains=instance)
            
        app_list = []
        for item in apps:
            item.Parent
            r = {}
            getFromChild = False
            r['Id'] = item.pk
            r['AppName'] = item.AppName
            r['Instance'] = item.Instance
            r['CreatedBy'] = item.CreatedBy
            r['CreatedDate'] = item.CreatedDate.strftime('%m/%d/%Y %I:%M:%S %p')
            r['UpdatedBy'] = item.UpdatedBy if item.UpdatedBy else None
            r['Type'] = 1 if item.Parent else 0
            r['UpdatedDate'] = item.UpdatedDate.strftime('%m/%d/%Y %I:%M:%S %p') if item.UpdatedDate else None
            r['Content'] = ''
            r['Filename'] = ''
            r['ConfigUrl'] = ''
            r['HealthUrl'] = ''
            conf = None
            if Configuration.objects.filter(Application=item).exists() :
                conf = Configuration.objects.filter(Application=item)[0]
                getFromChild = True
            if getFromChild==False:
                if Configuration.objects.filter(Application=item.Parent).exists() :
                    conf = Configuration.objects.filter(Application=item.Parent)[0]
            if conf:
                r['Content'] = conf.Content if conf.Content else '' 
                r['Filename'] = conf.Filename if conf.Filename else '' 
                r['ConfigUrl'] = conf.ConfigUrl if conf.ConfigUrl else '' 
                r['HealthUrl'] = conf.HealthUrl if conf.HealthUrl else '' 
            app_list.append(r)
            
        result['Result'] = app_list
    except Exception, ex:
        logger.exception(ex)
        result = {'Code': -1, 'Message': ex.__str__()}
    return result


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
    port = 8090
    if args.i:
        ip_addr = args.i
    if args.p:
        port = int(args.p)
    logging.info('Listening on %s:%s', ip_addr, port)
    WSGIServer((ip_addr, port), app).serve_forever()
