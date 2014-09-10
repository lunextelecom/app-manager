'''
Created on Aug 11, 2014

@author: Duc Le
'''
from django.db import models

def from_enum_choice(enum,all_captial = True):
    not_included_fields = ['choices','choices_dict'];
    choices_field = 'choices';
    choice_dict = {};
    if not choices_field in dir(enum):
        choices = sorted([(getattr(enum, f), f.upper() if all_captial else f.capit) for f in dir(enum) if (f not in not_included_fields) and (not f.startswith('_'))]);
        for k,v in choices:
            choice_dict[k] = v;
        setattr(enum,choices_field, choices);
        setattr(enum,'choices_dict', choice_dict);
    else:
        for k,v in enum.choices:
            choice_dict[k] = v;
        setattr(enum,'choices_dict', choice_dict);
    return getattr(enum, choices_field);

def to_enum_choice(enum,str_val,default = None):    
    try:
        str_val = str_val.upper();
        return getattr(enum, str_val);
    except:
        return default;


class ConfigMimeType(object):
    JSON = 'json'
    XML = 'xml'
    YAML = 'yaml'
    TEXT = 'txt'
    
    choices = [(JSON, 'application/json'),
               (XML, 'application/xml'),
               (YAML, 'application/yaml'),
               (TEXT, 'application/text')
               ]
    
class Application(models.Model):
    class Meta:
        db_table = 'app_application'
        unique_together = ['Instance']
    AppName = models.CharField(max_length=100)
    Instance = models.CharField(max_length=100,null=True)
    Parent = models.ForeignKey('Application', db_column='ParentId', null=True, related_name='children')# models.IntegerField(null=True)
    CreatedBy = models.CharField(max_length=20)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    UpdatedBy = models.CharField(max_length=20, null=True)
    UpdatedDate = models.DateTimeField(auto_now=True)    
    Latency = models.IntegerField(null=True)
    Ip = models.CharField(max_length=100,null=True)
    Enabled = models.IntegerField(default=1)

class Configuration(models.Model):
    class Meta:
        db_table = 'app_configuration'
        unique_together = ['Application']
    Application = models.ForeignKey(Application)
    ConfigUrl = models.CharField(max_length=100)
    Filename = models.TextField()
    Content = models.TextField()
    MimeType = models.CharField(max_length=20)
    CreatedBy = models.CharField(max_length=20)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    UpdatedBy = models.CharField(max_length=20, null=True)
    UpdatedDate = models.DateTimeField(auto_now=True)

class HealthConf(models.Model):
    class Meta:
        db_table = 'app_health_conf'
        unique_together = ['Application', 'Url']
    Application = models.ForeignKey(Application)
    Name = models.CharField(max_length=100)
    Url = models.CharField(max_length=100)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    
class HealthStatus(object):
    (RED, YELLOW, GREEN) = range(3)
    
    choices = [(RED, 'RED'),
               (YELLOW, 'YELLOW'),
               (GREEN, 'GREEN'),
               ]
class HealthType(object):
    (TELNET, LINK) = range(2)
    
    choices = [(TELNET, 'TELNET'),
               (LINK, 'LINK'),
               ]
class Health(models.Model):
    class Meta:
        db_table = 'app_health'
        unique_together = ['Application', 'MetricName', 'Function', 'Type']
    Application = models.ForeignKey(Application)
    Function = models.CharField(max_length=250)
    Status = models.SmallIntegerField(choices=from_enum_choice(HealthStatus),
                                    default=HealthStatus.GREEN)
    Type = models.SmallIntegerField(choices=from_enum_choice(HealthType),
                                    default=HealthType.LINK)
    MetricName = models.CharField(max_length=250)
    LastDowntime = models.DateTimeField(null=True)
    LastUptime = models.DateTimeField(null=True)
    LastPoll = models.DateTimeField(null=True)
    LastResponseTime = models.IntegerField(null=True)
    Last1HrTime = models.DateTimeField(null=True)
    Last24HrValue = models.CharField(max_length=500, null=True)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    UpdatedDate = models.DateTimeField(auto_now=True)