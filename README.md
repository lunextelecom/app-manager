app-manager
===========

Manage webapp configuration and health

## How does it work
###### Using Boostrap
```
1. start application bootstrap 
2. check and download new configuration, log from app-manager
3. starts application
```

###### Native support
```
1. starts application
2. check localfile version and remote version. Use the later one.
3. continue loading the application

Notes: during development it is not ideal to use remote, so there should be a start up option to use local file.
```

###### Bootstrap (For working with existing application)
This is a python script launcher that read configuration from app-manager and write it to file system.  It then set the environment variable and launch the application.  The advantage of using a bootstrapper is that all of the application does not need to have any dependency on this service.

###### Native support
Application can also communicate directly with this webservice for configuration.  In this case, it can take advantage of pull/push delivery which make configuration update easier to manage.  Depending on what configuration is change, the application itself must handle the change needed for setting changes.  For example, if it is the database connection that is change, the application should have logics to reload the database connections.

###### Application configuration
Application configuration and log configuration are stored in the server.  Each application can have multiple instance which can be install in multiple server. A unique instance can be define by appname@[instance_string].  A meaningful instance_string can be server:port so it is easier to manage webapp.

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
POST /app?instance=

#unregister application
DELETE /app?instance=
```

## Health Web Service
Centralized location for application to report health status.  Support for Dropwizard health.  Relay information to graphite for time series metric
* Health statistic
  * Aggreggate all webapp which manage configuration for.  
  * Build timeseries data, relay to graphite (polling )  
  * Notify when webapp goes down  

## UI
TBD
