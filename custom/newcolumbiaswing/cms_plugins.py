from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from cms.models.pluginmodel import CMSPlugin

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class MailchimpSignupPlugin(CMSPluginBase):
    model = CMSPlugin
    name = _('MailChimp Mailing List Sign Up')
    render_template = "mailchimp/mailchimp_signup.html"
    cache = True
    module = 'Forms'

    def render(self, context, instance, placeholder):
        ''' Add the context to sign up to the correct mailing list '''
        context = super(MailchimpSignupPlugin,self).render(context, instance, placeholder)

        context.update({
            'mailchimp_api_key': getattr(settings,'MAILCHIMP_API_KEY',None),
            'mailchimp_list_id': getattr(settings,'MAILCHIMP_LIST_ID',None),
        })

        return context


plugin_pool.register_plugin(MailchimpSignupPlugin)
