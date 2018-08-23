# Give this app a custom verbose name to avoid confusion
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class NewColumbiaAppConfig(AppConfig):
    name = 'newcolumbiaswing'
    verbose_name = _('New Columbia Swing Functions')
