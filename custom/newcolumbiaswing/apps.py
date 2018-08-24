# Give this app a custom verbose name to avoid confusion
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NewColumbiaAppConfig(AppConfig):
    name = 'newcolumbiaswing'
    verbose_name = _('New Columbia Swing Functions')

    def ready(self):
        ''' 
        Update the default placeholder configuration to set the default splash image and default title.
        '''
        from django.conf import settings

        if not isinstance(getattr(settings,'CMS_PLACEHOLDER_CONF',None),dict):
            settings.CMS_PLACEHOLDER_CONF = {}

        settings.CMS_PLACEHOLDER_CONF.update({
            'splash_image': {
                'name': 'New Columbia Swing Background Image',
                'limits': {
                    'global': 1,
                },
                'default_plugins':[
                    {
                        'plugin_type': 'TextPlugin',
                        'values':{
                            'body': 'https://via.placeholder.com/1920x400',
                        },
                    },
                ]
            },
            'splash_title': {
                'name': 'New Columbia Swing Front Page Title',
                'default_plugins':[
                    {
                        'plugin_type': 'TextPlugin',
                        'values': {
                            'body': 'New Columbia Swing',
                        }
                    }
                ]
            }
        })
