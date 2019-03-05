# Give this app a custom verbose name to avoid confusion
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from danceschool.core.utils.sys import isPreliminaryRun


class NewColumbiaAppConfig(AppConfig):
    name = 'newcolumbiaswing'
    verbose_name = _('New Columbia Swing Functions')

    def ready(self):
        from . import handlers
        from django.db import connection
        from danceschool.core.constants import getConstant, updateConstant

        if 'core_emailtemplate' in connection.introspection.table_names() and not isPreliminaryRun():
            from danceschool.core.models import EmailTemplate, get_defaultEmailName, get_defaultEmailFrom

            if (getConstant('promotions__lindy1TemplateID') or 0) <= 0:
                new_template, created = EmailTemplate.objects.get_or_create(
                    name=_('Post-Swing 1 Email Promotion With Vouchers'),
                    defaults={
                        'subject': _('Congratulations on Completing Swing 1!'),
                        'content': '',
                        'defaultFromAddress': get_defaultEmailFrom,
                        'defaultFromName': get_defaultEmailName,
                        'defaultCC': '',
                        'hideFromForm': True,}
                )
                # Update constant and fail silently
                updateConstant('promotions__lindy1TemplateID',new_template.id,True)
