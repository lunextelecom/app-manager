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
from lunex.utilities import httputils
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
        assert instance, 'Instance is invalid'
        try:
            #app_obj = Application.objects.get(Instance=instance)
            app_obj = Application.objects.get(Instance__icontains=instance)
        except Application.DoesNotExist:
            raise Exception('Instance [%s] does not exist' % instance)
        config_obj = Configuration.objects.get(Application=app_obj)
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
    
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}
    
@app.route('/config', method='PUT', name='save_config')
@app.route('/config/', method='PUT', name='save_config')
def save_config():
    try:
        params = dict(request.query.items())
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/config', method='DELETE', name='delete_config')
@app.route('/config/', method='DELETE', name='delete_config')
def delete_config():
    try:
        params = dict(request.query.items())
    except Exception, ex:
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/app', method='POST', name='register_app')
@app.route('/app/', method='POST', name='register_app')
@transaction.commit_manually
def register_app():
    try:
        params = dict(request.query.items())
        instance = params.get('instance', '').strip()
        assert instance, 'instance param is invalid'
        config_url = params.get('config_url', '').strip()
        assert config_url, 'config_url param is invalid'
        health_url = params.get('health_url', '').strip()
        assert health_url, 'health_url param is invalid'
        app_obj = Application(Instance=instance)
        app_obj.save()
        conf = Configuration(Application=app_obj, ConfigUrl=config_url, HealthUrl=health_url)
        
        conf.save()
        transaction.commit()
    except Exception, ex:
        transaction.rollback()
        logger.exception(ex)
        return {'Code': -1, 'Message': ex.__str__()}

@app.route('/app', method='DELETE', name='unregister_app')
@app.route('/app/', method='DELETE', name='unregister_app')
def unregister_app():
    try:
        params = dict(request.query.items())
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
        apps = Application.objects.all()
        if instance:
            apps = apps.filter(Instance=instance)
            
        app_list = []
        for item in apps:
            r = {}
            r['Id'] = item.pk
            r['Instance'] = item.Instance
            r['CreatedBy'] = item.CreatedBy
            r['CreatedDate'] = item.CreatedDate.strftime('%m/%d/%Y %I:%M:%S %p')
            r['UpdatedBy'] = item.UpdatedBy if item.UpdatedBy else None
            r['UpdatedDate'] = item.UpdatedDate.strftime('%m/%d/%Y %I:%M:%S %p') if item.UpdatedDate else None
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
    port = 8080
    if args.i:
        ip_addr = args.i
    if args.p:
        port = int(args.p)
    logging.info('Listening on %s:%s', ip_addr, port)
    WSGIServer((ip_addr, port), app).serve_forever()