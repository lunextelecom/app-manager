import httplib, urllib
import httplib2
import logging
logger = logging.getLogger('lunex.appmanagersvc.common.httputils')

def simple_http_request(server, method, path, params, headers, ssl=False):
    """\
    A quick way to post a form to a web server, without bothering about 
    connections and such. Returns the httplib.HTTPResponse object.
    server:  the web server along with optional port eg. 'www.google.com:80'
    method:  one of 'GET, 'POST'
    path:    address of the form. eg. '/search'
    params:  a dictionary of values to pass in the form.
    headers: a dictionary of additional to include/update. Default value is {
                'Content-type: 'application/x-www-form-urlencoded',
                'Accept': 'text/plain',
             }
    """
    reqheaders = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain',}
    reqheaders.update(headers)

    if ssl:
        conn = httplib.HTTPSConnection(server)
    else:
        conn = httplib.HTTPConnection(server)
        
    conn.request(method, path, urllib.urlencode(params), reqheaders)
    return conn.getresponse()

def send_request(method, path, body_data, headers={}):
    """\
    A quick way to send a request to a web server, without bothering about 
    connections and such. Returns the httplib.HTTPResponse object.
    server:  the web server along with optional port eg. 'www.google.com:80'
    method:  one of 'GET, 'POST', etc.
    path:    direct URL. eg. 'http://host/search'
    body_data:  string to pass to body of request.
    headers: a dictionary of additional to include/update. Default value is {
                'Accept':'text/xml',
                'Content-type':'text/xml',
             }
    """
    try:
        h = httplib2.Http("/tmp/.cache")
        
        if (body_data != ''):
            if len(headers.values()) == 0:
                headers={'Accept':'text/xml', 'Content-type':'text/xml'}
            resp, content = h.request(path, method, body=body_data, headers=headers)
        else:
            if len(headers.values()) == 0:
                headers={'Accept':'text/xml'}
            resp, content = h.request(path, method, body=' ', headers=headers)
    except Exception as inst:
        raise Exception('Error when send request. ' + inst.__str__())
    except:
        raise Exception('Error when send request.')
    
    return resp, content

def send_xml_request(method, path, body_data, headers={}):
    """\
    A quick way to send a XML request to a web server, without bothering about 
    connections and such. Returns the httplib.HTTPResponse object.
    server:  the web server along with optional port eg. 'www.google.com:80'
    method:  one of 'GET, 'POST', etc.
    path:    direct URL. eg. 'http://host/search'
    body_data:  string to pass to body of request.
    headers: a dictionary of additional to include/update. Default value is {
                'Accept':'text/xml',
                'Content-type':'text/xml',
             }
    """
    
    if (body_data != ''):
        reqheaders = {'Accept':'text/xml', 'Content-type':'text/xml'}
        reqheaders.update(headers)
        
        return send_request(method, path, body_data, reqheaders)
    else:
        reqheaders = {'Accept':'text/xml'}
        reqheaders.update(headers)
        
        return send_request(method, path, ' ', {'Accept':'text/xml'})
        
def send_json_request(method, path, body_data = '', headers={}):
    """\
    A quick way to send a JSON request to a web server, without bothering about 
    connections and such. Returns the httplib.HTTPResponse object.
    server:  the web server along with optional port eg. 'www.google.com:80'
    method:  one of 'GET, 'POST', etc.
    path:    direct URL. eg. 'http://host/search'
    body_data:  string to pass to body of request.
    headers: a dictionary of additional to include/update. Default value is {
                'Content-type': 'application/json',
             }
    """
    
    reqheaders = {'Content-type': 'application/json'}
    reqheaders.update(headers)
    logger.debug('send Json NOT GET request, body: ****************************')
    logger.debug(body_data)    
    return send_request(method, path, body_data, reqheaders)