app-manager
===========

Manage webapp configuration and health

## Todos 
```
[X] Design and Usage
[ ] Bootstrapper in python
[ ] Native Support
   [ ] define client library functions
   [ ] client library
      [ ] python
      [ ] java
   [ ] dropwizard plugin (use the client library)
   [ ] python plugin (use the client library)
[ ] app-manager webservice
   [X] REST API
   [ ] schema design
[ ] polling script (http status)
[ ] polling script dropwiz
```

## How does it work
###### Bootstrap (For working with existing application)
This is a python script launcher that read configuration from app-manager and write it to file system.  It then set the environment variable and launch the application.  The advantage of using a bootstrapper is that all of the application does not need to have any dependency on this service.

```
1. start application bootstrap script 
2. check current version(a local file with verison number)
3. compared with remote version, downlaod new configuration if needed 
4. update versions file
5. starts application
```

###### Native support (via plugins or library calls)
Application can also communicate directly with this webservice for configuration.  In this case, it can take advantage of pull/push delivery which make configuration update easier to manage.  Depending on what configuration is change, the application itself must handle the change needed for setting changes.  For example, if it is the database connection that is change, the application should have logics to reload the database connections.
Native support is done via a Plugin(bottle, Dropwizard) and direct library calls functions.

```
1. starts application which with plugins or calling library functions
2. check current version(a local file with verison number)
3. compared with remote version, downlaod new configuration if needed 
4. update versions file
5. Optional(register app) with callback for config_url, health_url
   these information can also be stored in the configuration.
6. continue with application initialization

Notes: during development it is not ideal to use remote, so there should be a start up option to use local file.
```

###### Application configuration
Application configuration and log configuration are stored in the server.  Each application can have multiple instance which can be install in multiple server. A unique instance can be define by appname@[instance_string].  A meaningful instance_string can be server:port so it is easier to manage webapp.
###### Minimal configuration
1. app-manager Url
2. instance name

## Configuration Web Service (App-Manager)
Web service providing storage and delivery of application configuration
* Storage
  * configuration for application instance
  * support inheritance for configuration.  simple base configuration can be made to avoid repeating.
* Delivery
  * remote client that request for it.  
  * push, application can be updated on the fly. 
```
#Getting configuration

#get only the version
GET /config/version?instance=

#get the configration
GET /config?instance=

#Saving configuration with body content-type can be application/json, application/yaml, application/xml, application/text
PUT /config?instance=

DELETE /config?instance=
#register application.  Once an app is register, the app manager will poll it for health statistic and push update configuration to it. 
POST /app?instance=&config_url=&health_url=&

#unregister application
DELETE /app?instance=
```

###### Webapp's config change
```
GET {config_url}?variable=newvalue
PUT {config_url}?variable=newvalue
body containing the variable changes or the entire configuration.
```
## Health Web Service
Centralized location for application to report health status.  Support for Dropwizard health.  Relay information to graphite for time series metric
* Health statistic
  * Aggreggate all webapp which manage configuration for.  
  * Build timeseries data, relay to graphite (polling )  
  * Notify when webapp goes down  

###### Old application
For old application, polling is consider anything url with http status 200 as up and anything else as down.

###### Drop wizard health
A drop wizard URL can be register during application startup.  
