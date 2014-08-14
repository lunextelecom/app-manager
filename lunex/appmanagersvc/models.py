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

class Configuration(models.Model):
    class Meta:
        db_table = 'app_configuration'
        unique_together = ['Application']
    Application = models.ForeignKey(Application)
    ConfigUrl = models.CharField(max_length=100)
    HealthUrl = models.CharField(max_length=100)
    Filename = models.TextField()
    Content = models.TextField()
    MimeType = models.CharField(max_length=20)
    CreatedBy = models.CharField(max_length=20)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    UpdatedBy = models.CharField(max_length=20, null=True)
    UpdatedDate = models.DateTimeField(auto_now=True)